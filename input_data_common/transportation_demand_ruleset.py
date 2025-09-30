import pandas as pd
import geopandas as gpd
import warnings
import numpy as np

# Extract the building information from the det file and convert it to a pandas dataframe
def extract_building_from_det(det):
            # Extract the required information and convert it to a pandas dataframe
            extracted_data = []

            for aim_id, info in det['Buildings']['Building'].items():
                general_info = info.get('GeneralInformation', {})
                extracted_data.append({
                    'AIM_id': aim_id,
                    'Latitude': general_info.get('Latitude'),
                    'Longitude': general_info.get('Longitude'),
                    'Population': general_info.get('Population'),
                    'PopulationRatio': general_info.get('PopulationRatio')
                })
            extracted_df = pd.DataFrame(extracted_data)
            return gpd.GeoDataFrame(extracted_df, geometry=gpd.points_from_xy(extracted_df.Longitude, extracted_df.Latitude), crs='epsg:4326')
# Aggregate the population in buildings to the closest road network node
def closest_neighbour(building_df, nodes_df):
    # Nikola: I think there is an issue with this method. I have multiple nodes and one building in the system and the population of the one building (which is in one of the nodes) is assigned to all nodes. So the sum of the population in nodes is multiple times higher than the actual population in the system. I assume the population from one building should only be linked to one (closest) node, not to multiple nodes.
    # Find the nearest road network node to each building
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        merged_df = building_df.sjoin_nearest(nodes_df, how = 'left')
        # merged_df = nodes_df.sjoin_nearest(building_df, how = 'left')
    merged_df = merged_df.drop(columns=['AIM_id', 'Latitude', 'Longitude', 'index_right'])
    merged_df = merged_df.fillna(0)
    merged_df['Population'] = merged_df['Population'] * merged_df['PopulationRatio']

    # Aggregate the population of the neareast buildings to the road network node
    return merged_df.groupby('node_id').agg({'x': 'first', 'y': 'first', 'geometry': 'first', 'Population': 'sum'}).reset_index()
# Function to add the population information to the nodes file
def find_population(nodes, det):
    # Extract the building information from the det file and convert it to a pandas dataframe
    building_df = extract_building_from_det(det)
    # Aggregate the population in buildings to the closest road network node
    updated_nodes_df = closest_neighbour(building_df, nodes)

    return updated_nodes_df  # noqa: RET504

def find_population_locality(loc_gdf, det):
    building_df = extract_building_from_det(det)

    building_df['Population']  = building_df['Population'] * building_df['PopulationRatio']

    loc_gdf = loc_gdf.sjoin(building_df, how = 'right', predicate='contains')

    return loc_gdf.groupby('loc_key').agg({'Population': 'sum','geometry': 'first'}).reset_index()



def update_od(initial_od, nodes_df, initial_r2d_dict, new_r2d_dict):
    # Find the locality id of each node
    import json, os
    # input_data_dir = "/Users/jinyanzhao/Documents/R2D/LocalWorkDir/pyrecodes/input_data"
    input_data_dir = os.getenv("pyrecodes_input_dir_common")
    system_config_file = os.path.join(input_data_dir, "Alameda_SystemConfiguration.json")
    with open(system_config_file, 'r') as f:
        system_config = json.load(f)
    loc_keys = []
    loc_geometries = []
    for loc_key, loc in system_config['Content'].items():
         geojson_file_i = loc['Coordinates']['GeoJSON']['Filename']
         geojson_file_i = os.path.join(input_data_dir, geojson_file_i)
         loc_gdf = gpd.read_file(geojson_file_i)
         loc_keys.append(loc_key)
         loc_geometries.append(loc_gdf.geometry.values[0])
    loc_gdf = gpd.GeoDataFrame({'loc_key': loc_keys, 'geometry': loc_geometries}, crs='epsg:4326')

    orig_nodes = nodes_df.loc[initial_od['origin_nid'].values,:]
    orig_nodes['trip_index'] = range(0, len(orig_nodes))
    orig_nodes = loc_gdf.sjoin(orig_nodes, how = 'right', predicate='contains')
    trips_orig_outside = orig_nodes['trip_index'][orig_nodes['loc_key'].isna()].values

    dest_nodes = nodes_df.loc[initial_od['destin_nid'].values,:]
    dest_nodes['trip_index'] = range(0, len(dest_nodes))
    dest_nodes = loc_gdf.sjoin(dest_nodes, how = 'right', predicate='contains')
    dest_nodes = dest_nodes.iloc[orig_nodes[orig_nodes['loc_key'].isna()]['trip_index'].values,:] # remove the trips that has been classified using orig_nodes
    trips_dest_outside = dest_nodes['trip_index'][dest_nodes['loc_key'].isna()].values

    trips_starting_at_localities = orig_nodes[['loc_key', 'trip_index']].groupby('loc_key').agg(list)['trip_index'].to_dict()
    trips_ending_at_localities = dest_nodes[['loc_key', 'trip_index']].groupby('loc_key').agg(list)['trip_index'].to_dict()
    
    old_population_locality = find_population_locality(loc_gdf, initial_r2d_dict)
    new_population_locality = find_population_locality(loc_gdf, new_r2d_dict)
    old_population_locality['delta_population'] = new_population_locality['Population'] - old_population_locality['Population']
    population_change = old_population_locality[['loc_key', 'delta_population']].set_index('loc_key')['delta_population'].to_dict()
    old_population_locality = old_population_locality.set_index('loc_key')

    # population change percentage at each node
    trips_index_set = set()
    for i in loc_gdf.index:
        loc_key = loc_gdf.loc[i, 'loc_key']
        ### for debug
        # pop_change_i = 0
        pop_change_i = population_change.get(loc_key, 0)
        # The population did not change, the OD starting and ending at this node does not change
        if pop_change_i == 0:
            trips_index_set = trips_index_set.union(set(trips_starting_at_localities.get(loc_key, [])))
            trips_index_set = trips_index_set.union(set(trips_ending_at_localities.get(loc_key, [])))
        # If the population changed and if the original OD starting and ending at this node is zero,
        # Generate new OD starting and ending at this node. This is considered impossible in this
        # implementation as new population can only be generated at nodes with non-zero pre-event population
        elif old_population_locality.loc[loc_key, 'Population'] == 0:
            print(f'Warning: New population generated in {loc_key}, which had zero pre-event population')
        # If the population changed and if the original OD starting and ending at this node is not zero,
        # Modify the trips starting and ending at this node according to the population change percentage
        else:
            change_percentage = pop_change_i / old_population_locality.loc[loc_key, 'Population']
            origin_trips = trips_starting_at_localities.get(loc_key, [])
            origin_trips_remove = np.random.choice(origin_trips, int(len(origin_trips) * np.abs(change_percentage)), replace=False)
            origin_trips = set(origin_trips) - set(origin_trips_remove)
            destin_trips = trips_ending_at_localities.get(loc_key, [])
            destin_trips = list(set(destin_trips) - set(trips_starting_at_localities.get(loc_key, [])))
            destin_trips_remove = np.random.choice(destin_trips, int(len(destin_trips) * np.abs(change_percentage)), replace=False)
            destin_trips = set(destin_trips) - set(destin_trips_remove)
            trips_index_set = trips_index_set.union(origin_trips).union(destin_trips)
    trips_index_set = trips_index_set.union(set(trips_orig_outside)).union(set(trips_dest_outside))
    trips_index_set = sorted(trips_index_set)


    # trips_starting_at_nodes = initial_od.reset_index()[['origin_nid', 'index']].groupby(
    #     'origin_nid').agg(list).to_dict()['index']
    # trips_ending_at_nodes = initial_od.reset_index()[['destin_nid', 'index']].groupby(
    #     'destin_nid').agg(list).to_dict()['index']
    # # old population at each node
    # old_population = find_population(nodes_df, initial_r2d_dict)
    # # new population at each node
    # new_population = find_population(nodes_df, new_r2d_dict)
    # old_population['delta_population'] = new_population['Population'] - old_population['Population']
    # population_change = old_population[['node_id', 'delta_population']].set_index('node_id')['delta_population'].to_dict()
    # old_population = old_population.set_index('node_id')
    # # population change percentage at each node
    # trips_index_set = set()
    # for i in nodes_df.index:
    #     node_id = nodes_df.loc[i, 'node_id']
    #     ### for debug
    #     # pop_change_i = 0
    #     pop_change_i = population_change.get(node_id, 0)
    #     # The population did not change, the OD starting and ending at this node does not change
    #     if pop_change_i == 0:
    #         trips_index_set = trips_index_set.union(set(trips_starting_at_nodes.get(node_id, [])))
    #         trips_index_set = trips_index_set.union(set(trips_ending_at_nodes.get(node_id, [])))
    #     # If the population changed and if the original OD starting and ending at this node is zero,
    #     # Generate new OD starting and ending at this node. This is considered impossible in this
    #     # implementation as new population can only be generated at nodes with non-zero pre-event population
    #     elif old_population.loc[node_id, 'Population'] == 0:
    #         print(f'Warning: New population generated at node {node_id}, which had zero pre-event population')
    #     # If the population changed and if the original OD starting and ending at this node is not zero,
    #     # Modify the trips starting and ending at this node according to the population change percentage
    #     else:
    #         change_percentage = pop_change_i / old_population.loc[node_id, 'Population']
    #         origin_trips = trips_starting_at_nodes.get(node_id, [])
    #         origin_trips = np.random.choice(origin_trips, int(len(origin_trips) * (1+change_percentage)), replace=False)
    #         destin_trips = trips_ending_at_nodes.get(node_id, [])
    #         destin_trips = np.random.choice(destin_trips, int(len(destin_trips) * (1+change_percentage)), replace=False)
    #         trips_index_set = trips_index_set.union(set(origin_trips)).union(set(destin_trips))
    # trips_index_set = sorted(trips_index_set)
    return initial_od.loc[trips_index_set, :]