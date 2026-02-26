import sys, os

sys.path.append(os.path.dirname(sys.argv[0]))

import argparse

from interface_cpp import DrawingProcess

def parserArgument():
    ap = argparse.ArgumentParser()

    ap.add_argument("SourceFilesPath", type=str, help="The path of the files to read problem info and trials points.")
    ap.add_argument("ProblemFileName", type=str, help="The file with problem info.")
    ap.add_argument("TrialsFileName", type=str, help="The file with trials points.")
    
    ap.add_argument("-PlotFileName", "--PlotFileName", type=str, default="GlobalizerPicture.png", help="The name of the file to save the image.")
    
    ap.add_argument("-ShowFigure", "--ShowFigure", action='store_true', help="A flag indicating the need to open the resulting drawing in an interactive window on the screen")
    ap.add_argument("-PointsBelowGraph", "--PointsBelowGraph", action='store_true', help="A flag indicating the need to shift the trial points in the figure below the graph.")
    #ap.add_argument("-DontShowPoints", "--DontShowPoints", action='store_true', help="A flag indicating the need to hide trial points.")
    
    ap.add_argument("-FigureType", "--FigureType", type=str, default="LevelLayers", help="The type of visualization of the target function (available modes : 0 - LevelLayers, 1 - Surface)")
    ap.add_argument("-CalcsType", "--CalcsType", type=str, default="Interpolation", help="The type of value calculations for visualizing the objective function (available modes: ObjectiveFunction, Approximation, Interpolation, ByPoints, OnlyPoints)")
    
    ap.add_argument("-Eps", "--Epsilon", type=float, default=0.01, help="Accuracy of solve.")
    ap.add_argument("-x1", "--x1", type=int, default=0, help="First parameter number for visualization.")
    ap.add_argument("-x2", "--x2", type=int, default=1, help="Second parameter number for visualization.")

    return ap

def read_args():
    ap = parserArgument()
    args = vars(ap.parse_args())

    if (args['SourceFilesPath'] is None) or (args['TrialsFileName'] is None) or (args['ProblemFileName'] is None):
        ap.print_help()
    else:
        ap.print_help()
        path = str(args['SourceFilesPath'])
        if path[-1] != '/':
            path += '/'
        trials_file_name = str(args['TrialsFileName'])
        problem_file_name = str(args['ProblemFileName'])
        output_file_name = str(args['PlotFileName'])
        
        eps = float(args['Epsilon'])
        plot_type = str(args['FigureType'])
        obj_func_type = str(args['CalcsType'])

        if plot_type == 'LevelLayers':
            plot_type = 'lines layers'
        else: 
            plot_type = 'surface'

        if obj_func_type == 'ObjectiveFunction':
            obj_func_type = 'objective function'
        elif obj_func_type == 'Approximation':
            obj_func_type = 'approximation'
        elif obj_func_type == 'Interpolation':
            obj_func_type = 'interpolation'
        elif obj_func_type == 'ByPoints':
            obj_func_type = 'by points'
        else:
            obj_func_type = 'only points'

        params = list({int(args['x1']), int(args['x2'])})

        if args['PointsBelowGraph'] is None:
            displacement_of_points = False
        else:
            displacement_of_points = True

        if args['ShowFigure'] is None:
            figure_show = False
        else:
            figure_show = True

    return path, trials_file_name, problem_file_name, eps, plot_type, obj_func_type, params, displacement_of_points, output_file_name, figure_show

if __name__ == "__main__":
    print("Start ", str(sys.argv[0]), "...")

    path, trials_file_name, problem_file_name, eps, plot_type, obj_func_type, params, displacement_of_points, output_file_name, figure_show = read_args()

    dp = DrawingProcess(path, trials_file_name, problem_file_name, eps)

    dp.draw_plot(plotter_type=plot_type,
                 object_function_plotter_type=obj_func_type,
                 parameters_numbers=params,
                 is_points_at_bottom=displacement_of_points,
                 output_file=output_file_name,
                 is_need_show_figure=figure_show
                 )
    
    print("Picture was saved in", path + output_file_name)
