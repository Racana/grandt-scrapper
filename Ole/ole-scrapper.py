import argparse
from selenium import webdriver

def run():
    driver = webdriver.Chrome(r'C:\Users\El_Ra\Google Drive\Python\automate_online-materials\chromedriver_win32\chromedriver.exe')
    driver.get('https://www.ole.com.ar/estadisticas/futbol/primera-division.html')
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Webscrapper for Ole sport magazine, scrapping Superliga data')
    parser.add_argument('--jornada', metavar='Week to scrape', type=int, 
                        help='Indicate the week that you would like to scrape', default=None)
    parser.add_argument('--arg2')
    args = parser.parse_args()

    print(args.jornada)
    print(args.arg2)

    my_dict = {'jornada': args.jornada, 'arg2': args.arg2}
    print(my_dict)

    run()


