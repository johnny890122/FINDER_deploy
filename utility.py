# import requests 
# import pygsheets
# from bs4 import BeautifulSoup
# import pandas as pd

# url = input("Enter the link: ")
# soup = BeautifulSoup(requests.get(url).text, 'html.parser')

# links_text = soup.find_all('a', attrs={"class": "participant-link"})
# href_lst = [ link.attrs["href"] for link in links_text ]

# df = pd.DataFrame({"id": [ i+1 for i in range(len(href_lst))], "link": href_lst})

# auth_file = "finderlink-381806-aa232dd1eff5.json"
# gc = pygsheets.authorize(service_file = auth_file)

# try: 
# 	# setting sheet
# 	sheet_url = "https://docs.google.com/spreadsheets/d/15t8MjE9mLmHGQDWzGGqEPiri402DKU1Ux8EX9XyxwcA/" 
# 	sheet = gc.open_by_url(sheet_url)
# 	sheet.worksheet_by_title("link").clear()
# 	sheet.worksheet_by_title("link").set_dataframe(df, start = "A1") 
# 	print("成功上傳連結！")
# except:
# 	print("失敗！")

