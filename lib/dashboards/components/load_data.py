import numpy as np
import pandas as pd


def load_and_prepare_data(json_data):
    """Load and prepare input data

    Args:
    json_data: Parsed JSON data containing optimization parameters, task info,
        search results and solution details.

    Returns:
        A dictionary containing prepared optimization data, solution
        statistics, parameter metadata and dashboard-ready data frames.
    """

    data = json_data

    task = data['Task'][0]
    solution = pd.DataFrame(data['solution'])

    search_data = pd.DataFrame(data['SearchDataItem']).rename(
        columns={'__z': 'objective_func'}
    )

    fnames = [*pd.DataFrame(task['float_variables'])]
    dnames = [*pd.DataFrame(task['discrete_variables'])]

    float_parameters_names = [f"{name} [c]" for name in fnames]
    discrete_parameters_names = [f"{name} [d]" for name in dnames]

    parameters_names = float_parameters_names + discrete_parameters_names

    solution_accuracy = float(solution['solution_accuracy'].squeeze())
    accuracy_precision = _get_accuracy_precision(solution_accuracy)

    best_trial_fevs = pd.DataFrame(data['best_trials']).rename(columns={'__z': 'objective_func'})

    best_value = best_trial_fevs['objective_func'][0]

    best_float_point_dict = dict(zip(
        float_parameters_names,
        [
            round(elem, accuracy_precision) for elem in best_trial_fevs['float_variables'][0]
        ]
    ))

    best_discrete_point_dict = dict(zip(
        discrete_parameters_names,
        best_trial_fevs['discrete_variables'][0]
    ))

    iters_times = __convert_times(search_data["creation_time"].to_list())

    search_data, search_data_original = __restruct_dataframe(
        search_data,
        float_parameters_names,
        discrete_parameters_names
    )
    parameters_importance = __calculate_parameters_importance(search_data, parameters_names)

    return {
        'eps': data['Parameters'][0]['eps'],
        'r' : data['Parameters'][0]['r'],
        'iters_limit': data['Parameters'][0]['iters_limit'],
        'start_point': data['Parameters'][0]['start_point'],
        'task_name': task['name'],
        'functional_count': len(data['SearchDataItem'][0]["function_values"]),
        'float_parameters_bounds': task['float_variables'],
        'params_float': float_parameters_names,
        'params_discrete': discrete_parameters_names,
        'params_all': parameters_names,
        'accuracy': solution_accuracy,
        'trial_number': int(solution['number_of_trials'].squeeze()),
        'global_iter_number': int(solution['number_of_global_trials'].squeeze()),
        'local_iter_number': int(solution['number_of_local_trials'].squeeze()),
        'solve_time': float(solution['solving_time'].squeeze()),
        'best_trial_number': int(solution['num_iteration_best_trial'].iloc[0][0]),
        'best_trials': best_trial_fevs,
        'best_value': best_value,
        'best_float_point_dict': best_float_point_dict,
        'best_discrete_point_dict': best_discrete_point_dict,
        'iters_times': iters_times,
        'parameters_importance': parameters_importance,
        'search_data': search_data,
        'search_data_original': search_data_original
    }


def __convert_times(iters_times):
    isFirst = 1
    first_not_zero_time = 0
    update_times = []
    for elem in iters_times:
        if elem != 0 and isFirst:
            first_not_zero_time = elem
            isFirst = 0
        if elem != 0:
            elem -= first_not_zero_time
        update_times.append(elem)

    return update_times

def __restruct_dataframe(df, float_parameters_names, discrete_parameters_names):
    FVs = pd.DataFrame(
        df['float_variables'].to_list(),
        columns=float_parameters_names,
        index=df.index
    )

    DVs = pd.DataFrame(
        df['discrete_variables'].to_list(),
        columns=discrete_parameters_names,
        index=df.index
    )

    df = df[[ "objective_func", "x", "delta", "globalR", "localR", "index" ]]

    df = pd.concat([DVs, df], axis=1, join='inner')
    df = pd.concat([FVs, df], axis=1, join='inner')

    df.insert(loc=0, column='trial', value=np.arange(1, len(df) + 1))

    df_original = df.copy()

    df.drop(df[df['objective_func'] >= 1.797692e+308].index, inplace=True)
    df.drop(df[df['index'] == - 2].index, inplace=True)

    return df, df_original


def __calculate_parameters_importance(df, parameters_names):
    min_obj_func = min(df['objective_func'])
    max_obj_func = max(df['objective_func'])
    obj_func_range = max_obj_func - min_obj_func

    importance = []
    for parameter in parameters_names:
        uniq_parameter_values = df[parameter].unique()
        importance_value = 0
        for value in uniq_parameter_values:
            data = df.loc[df[parameter] == value]
            importance_value += (max(data['objective_func']) - min(data['objective_func']))

        vals_count = len(uniq_parameter_values)
        normalization_factor = vals_count * obj_func_range
        normalized_importance = importance_value / normalization_factor
        importance.append(round(normalized_importance, 2))

    return importance

def _get_accuracy_precision(accuracy):
    precision = 0
    while accuracy < 1:
        accuracy *= 10
        precision += 1
    return precision
