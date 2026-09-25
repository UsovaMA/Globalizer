import os

import numpy as np


class Reader:
    """
    Базовый класс читателей
    """
    def load(self):
        pass

    def read_first_line(self, line):
        pass

    def read_second_line(self, line):
        pass

    def read_last_line(self, line):
        pass

    def read_line(self, line):
        pass

class TrialReader(Reader):
    def __init__(self, dir, file_for_reading):
        self.__file_path = os.path.join(dir, file_for_reading)

    def load(self):
        with open(self.__file_path) as file:
            iters_count = 0
            sol_x = []
            sol_z = None
            x = []
            z = []
            x_nc = []
            z_nc = []
            x_nce = []
            cc = []

            isFirst = True
            for line in file:
                if isFirst:
                    first_line_data =self.read_first_line(line)
                    iters_count, num_of_func, cc = first_line_data
                    isFirst = False
                    continue
                if iters_count == 0:
                    last_line_data = self.read_last_line(line, num_of_func)
                    sol_x, sol_z = last_line_data
                    break

                line_data = self.read_line(
                    line, num_of_func, x, z, x_nc, z_nc, x_nce, cc
                )

                x, z, x_nc, z_nc, x_nce, cc = line_data

                iters_count = iters_count - 1

        uncalculated_points_count = len(x_nce)

        print(f"Uncalculate point\'s count: {uncalculated_points_count}")

        return x, z, sol_x, sol_z, x_nc, z_nc, cc, x_nce

    def read_first_line(self, line):
        splitedline = line.split(' ')
        iters_count = int(splitedline[0])
        num_of_func = int(splitedline[1])

        constraints_count = max(1, (num_of_func - 1) * 2)

        cc = [[] for _ in range(constraints_count)]

        return iters_count, num_of_func, cc

    def read_last_line(self, line, num_of_func):
        splitedline = line.split(' | ')
        point = splitedline[0].split(' ')
        value = splitedline[1].split(' ')

        sol_x = [float(point[j]) for j in range(len(point))]
        sol_z = float(value[num_of_func - 1])

        return sol_x, sol_z

    def read_line(self, line, num_of_func, x, z, x_nc, z_nc, x_nce, cc):
        splitedline = line.split(' | ')

        value = splitedline[1].split(' ')
        point = splitedline[0].split(' ')

        xi = [float(point[j]) for j in range(len(point))]

        if (value[0] == '|'):
            x_nce.append(xi)
        elif len(value) >= num_of_func:
            zi = float(value[num_of_func - 1])
            x.append(xi)
            z.append(zi)
        else:
            #zi = float(value[len(value) - 1])
            x_nc.append(xi)
            z_nc.append(0)  # заглушка, лишний параметр

        if (value[0] != '|'):
            i = 0
            while i != len(value) - 1:
                cc[i * 2].append(xi)
                cc[i * 2 + 1].append(float(value[i]))
                i += 1

        return x, z, x_nc, z_nc, x_nce, cc

class ProblemReader(Reader):
    def __init__(self, dir, file_for_reading):
        self.__file_path = os.path.join(dir, file_for_reading)

    def load(self):
        with open(self.__file_path) as file:
            dim = 0
            lb = []
            rb = []
            x = []
            z = []
            c = []
            is_objective_calc = False
            is_constraints_calc = False
            isFirst = True
            isSecond = True

            for line in file:
                if isFirst:
                    first_line_data = self.read_first_line(line)
                    dim, lb, rb = first_line_data
                    isFirst = False
                    continue
                if isSecond:
                    second_line_data = self.read_second_line(line)
                    is_objective_calc, is_constraints_calc = second_line_data
                    isSecond = False
                    continue

                if is_objective_calc or is_constraints_calc:  # необязательная проверка, для надежности от пустых строк
                    line_data = self.read_line(line, is_objective_calc, x, z, c)
                    x, z, c = line_data

        return dim, lb, rb, x, z, c


    def read_first_line(self, line):
        lb = []
        rb = []

        splitedline = line.split()
        dim = int(splitedline[0])
        lb_line = splitedline[1].split('_')
        rb_line = splitedline[2].split('_')
        lb.extend(float(val) for val in lb_line)
        rb.extend(float(val) for val in rb_line)

        return dim, lb, rb

    def read_second_line(self, line):
        splitedline = line.split(' ')
        is_objective_calc = bool(int(splitedline[0]))
        is_constraints_calc = bool(int(splitedline[1]))

        return is_objective_calc, is_constraints_calc

    def read_line(self, line, is_objective_calc, x, z, c):
        splitedline = line.split(' | ')
        point = splitedline[0].split(' ')

        xi = [float(point[j]) for j in range(len(point))]

        x.append(xi)

        if is_objective_calc:
            values = splitedline[len(splitedline) - 1].split(' ')

            if abs(float(values[0])) > 1.6e308 or not np.isfinite(float(values[0])):
                z.append(np.nan)
            else:
                z.append(float(values[0]))

        constraints_count = len(splitedline) - is_objective_calc


        ci = [
            float(splitedline[j].split(' ')[0])
            for j in range(1, constraints_count)
        ]

        if len(ci) > 0:
            c.append(ci)

        return x, z, c
