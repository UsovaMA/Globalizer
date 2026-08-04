from GlobalizerDashboard import StaticDashboard
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Визуализирует процесс оптимизации из JSON-файла для аналитики полученного решения.'
    )

    parser.add_argument(
        'dashboardData', 
        type=str, 
        help='Путь к файлу .json с данными для построения дашборда, полученному средствами globalizer'
    )
    
    args = parser.parse_args()

    dashboard = StaticDashboard(args.dashboardData)
    
    dashboard.launch()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: укажите путь к JSON-файлу с данными для дашборда.")
        print(f"Использование: python {sys.argv[0]} <имя_файла.json>")
        exit(1)

    main()