import requests
import csv
import os
import wget
from bs4 import BeautifulSoup
from word2number import w2n


# Scraping function to extract data from each book's page and save them in csv files
def scrap_book(url, category):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Data extraction
    title = soup.h1.string
    upc = soup.find_all("td")[0].string
    price_inc_tax = soup.find_all("td")[3].string.replace('£', '')
    price_exc_tax = soup.find_all("td")[2].string.replace('£', '')
    number_available = int(''.join(filter(str.isdigit, soup.find_all("td")[5].string)))
    if soup.find("div", {"id": "product_description"}):
        description = soup.find("article", class_="product_page").find_all("p")[3].string
    else: description = ''
    review = w2n.word_to_num(soup.find("p", class_="star-rating")['class'][1])
    image = soup.img['src'].replace("../..", "https://books.toscrape.com")

    # Appending each category's CSV file with the book's data
    book_data = [url, upc, title, price_inc_tax, price_exc_tax, number_available, description, category,
                 review, image]
    with open('data/' + category + '.csv', 'a', encoding='utf8', errors='replace') as csv_file:
        csv.writer(csv_file, delimiter=',', lineterminator='\n').writerow(book_data)

    # Saving the image for each book, deleting it first if already existing in the images folder
    filename = 'images/' + os.path.basename(image)
    if os.path.exists(filename): os.remove(filename)
    wget.download(image, out='images/', bar=False)

    print(title)


# Initial page request and folders creation
page = requests.get('http://books.toscrape.com/index.html')
soup = BeautifulSoup(page.content, 'html.parser')
if not os.path.exists('data/'): os.makedirs('data/')
if not os.path.exists('images/'): os.makedirs('images/')

# Pulling the list of all categories present on the front page
categories = {}
for a in soup.find('div', {'class': 'side_categories'}).ul.find_all('a'):
    if 'books_1' not in a.get('href'):
        categories[a.text.replace('\n', '').replace('  ', '')] = 'http://books.toscrape.com/' + a.get('href')

# Loop for each category
for category, cat_url in categories.items():
    page = requests.get(cat_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Creation of CSV files for each category, with column headers
    csv_headers = ['product_page_url', 'universal_product_code', 'title', 'price_including_tax', 'price_excluding_tax',
                   'number_available', 'product_description', 'category', 'review_rating', 'image_url']

    with open('data/' + category + '.csv', 'w', encoding='utf8', errors='replace') as csv_init:
        writer = csv.DictWriter(csv_init, delimiter=",", fieldnames=csv_headers, lineterminator='\n')
        writer.writeheader()
        print('\n---------------  Scraping category: ' + category + '  ---------------')

    # Detection of multiple pages if present
    if soup.find('ul', {'class': 'pager'}):
        pages_number = int(soup.find('li', {'class': 'current'}).text.strip()[-1])
    else:
        pages_number = 1

    # Loop for each book in a category
    i = 0
    while i < pages_number:
        # Scraping function call for each book, sending URL and category as arguments
        for book in soup.find_all('article'):
            book_url = book.h3.a.get('href').replace('../../../', 'http://books.toscrape.com/catalogue/')
            scrap_book(book_url, category)
        i += 1
        # Updating content if a next page is present
        if pages_number > 1:
            next_page = requests.get(cat_url.replace('index.html', 'page-' + str(i + 1) + '.html'))
            soup = BeautifulSoup(next_page.content, 'html.parser')
