A project in which I practiced WebScrapping using Python and BeautifulSoup. I had to scrape events' data from a real site (I chose https://www.turismo.gov.br/agenda-eventos/views/calendario.php, an official government site) and then save said data into a SQL database. When I found out the website had some dynamic elements that I also needed to access, I had to automate the process using Selenium, which allowed me to simulate the mouse clicks necessaries to make the elements become visible.

![image](https://github.com/user-attachments/assets/6e29de3b-1ed2-42fb-986e-407b530ea0d4)
The site has all the cultural events up until the end of the current year, which added up to around 400 events.

![image](https://github.com/user-attachments/assets/82497349-bec0-4b75-8b8b-32704a5acc3e)

The script will only run if one or more database tables are empty. So if a fresh set of data is needed, we only need to create a new table/delete an existing one.

By the end of the script, I had 3 tables full of data such as events' names, dates, locations and metadata...
![image](https://github.com/user-attachments/assets/bc0362a6-ec68-4403-b098-52253d31f2d8)
![image](https://github.com/user-attachments/assets/5f56e08e-a1a4-459e-9ce9-e6d37e31ec95)
![image](https://github.com/user-attachments/assets/4c85539c-1170-4b34-9aa8-2be893de6d12)


...which then allowed me to run some SQL queries.
![image](https://github.com/user-attachments/assets/154101e1-086e-4e80-b88e-a13072afb14b)
![image](https://github.com/user-attachments/assets/e9fed401-2d64-4d1c-913a-da6c0f455c79)
![image](https://github.com/user-attachments/assets/dd97152d-7e99-45f5-a604-32e37e9e024d)


