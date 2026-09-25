*ПРИМЕРЫ ЗАПУСКА PLOTTER*

**Простейшие случаи**

* отрисовка с параметрами по умолчанию
(рисует интерполяцию линий уровня (2D+) / интерполяцию точек испытаний (1D)):
```
python start_py.py .\data\examples rastrigin_2D_problem_info.txt rastrigin_2D_trials.txt
```

* отрисовка с заданием имени для рисунка:
```
python start_py.py .\data\examples rastrigin_2D_problem_info.txt rastrigin_2D_trials.txt -pfn Rastrigin2D.png
```

* отрисовка с настройкой границ рисунка (для приближения интересующей области):
```
python start_py.py .\data\examples rastrigin_2D_problem_info.txt rastrigin_2D_trials.txt -b " -0.75_-0.8 0.85_0.9" -pfn Rastrigin2D_zoom.png
```

* отрисовка по части переменных
```
python start_py.py .\data\examples Rastrigin_3D_problem_info.txt Rastrigin_3D_trials.txt --PlotFileName Rastrigin_3D_surf_params_0_2.png -ft Surface --PointsBelowGraph -x1 0 -x2 2
```

* для отрисовки поверхности и отображением окна Figure для возможности вращения и сохранения под нужным углом:
```
python start_py.py .\data\examples RastriginInt_4D_2_2_problem_info.txt RastriginInt_4D_2_2_trials.txt --PlotFileName RastriginInt_4D_2_2.png --FigureType Surface --ShowFigure
```

* для отрисовки многомерной задачи, но с единственным непрерывным параметром / визуализация по одному конкретному параметру:
(так как задача решалась без просчета сетки целевой функции, режим ObjectiveFunction не доступен):
```
python start_py.py .\data\examples RastriginInt_NC_4D_3_1_problem_info.txt RastriginInt_NC_4D_3_1_trials.txt --PlotFileName RastriginInt_NC_4D_3_1_intepr.png  --1D -ct Interpolation
```
```
python start_py.py .\data\examples RastriginInt_NC_4D_3_1_problem_info.txt RastriginInt_NC_4D_3_1_trials.txt --PlotFileName RastriginInt_NC_4D_3_1_approx.png  --1D -ct Approximation
```
```
python start_py.py .\data\examples RastriginInt_NC_4D_3_1_problem_info.txt RastriginInt_NC_4D_3_1_trials.txt --PlotFileName RastriginInt_NC_4D_3_1_by_points.png  --1D -ct ByPoints
```

* со смещением точек под график:
```
python start_py.py .\data\examples RastriginInt_NC_4D_3_1_problem_info.txt RastriginInt_NC_4D_3_1_trials.txt --PlotFileName RastriginInt_NC_4D_3_1.png  --1D --PointsBelowGraph -ct Interpolation
```

* отрисовка задачи с ограничениями в виде линий уровня с закрашиванием допустимой области
(так как есть сетка есть возможность нарисовать ограничения и/или целевую функцию по ней):
```
python start_py.py .\data\examples Strongin3C_2D_problem_info.txt Strongin3C_2D_trials.txt --PlotFileName Strongin3C_2D.png --FillFeasibleRegion
```
```
python start_py.py .\data\examples Strongin3C_2D_problem_info.txt Strongin3C_2D_trials.txt --PlotFileName Strongin3C_2D_objf_objc.png --FillFeasibleRegion -ct ObjectiveFunction -ctc ObjectiveFunction
```
```
python start_py.py .\data\examples Strongin3C_2D_problem_info.txt Strongin3C_2D_trials.txt --PlotFileName Strongin3C_2D_interpf_objc.png --FillFeasibleRegion -ctc ObjectiveFunction
```

* отрисовка задачи с ограничениями в виде поверхности:
```
python start_py.py .\data\examples Strongin3C_2D_problem_info.txt Strongin3C_2D_trials.txt --PlotFileName Strongin3C_2D_surface.png -ft Surface --PointsBelowGraph
```

*отрисовка задачи с точками невычислимости
(автоматизировано рисует стандартными командами):
```
python start_py.py .\data\examples Strongin3C_NC_problem_info.txt Strongin3C_NC_trials.txt --PlotFileName Strongin3C_NC.png
```

* отрисовка задачи со скрытыми ограничениями
(в режимах профиль ObjectiveFunction и Interpolation рисуется только в области вычислимости):
```
python start_py.py .\data\examples Strongin3HC_problem_info.txt Strongin3HC_trials.txt --PlotFileName Strongin3HC_obj.png -ct ObjectiveFunction
```
```
python start_py.py .\data\examples Strongin3HC_problem_info.txt Strongin3HC_trials.txt --PlotFileName Strongin3HC_surface_obj.png -ft Surface --PointsBelowGraph -ct ObjectiveFunction
```
```
python start_py.py .\data\examples Strongin3HC_problem_info.txt Strongin3HC_trials.txt --PlotFileName Strongin3HC_surface_interp.png -ft Surface --PointsBelowGraph -ct Interpolation 
```




