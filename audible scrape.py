import re
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import datetime
import time

def get_authors(text, string=True):
  try:
    return text.split('by: ')[1]
    
  except:
    return None 

def generate_link(page=1, main_category="Science Fiction & Fantasy", genre="Science Fiction", author_author="", keywords="", narrator="", publisher="", sort="", title="", pageSize=50, language="English"):


  base_url = "https://www.audible.com/search?"
  main_category_dict = {
    "Science Fiction & Fantasy": "20956260011",
    "Romance": "2226655011",
    "Mystery, Thriller & Suspense": "18580609011",

  }

  genre_dict = {
    "Science Fiction": "18580606011",
    "Fantasy": "18580607011",
    "Sci-Fi & Fantasy Anthologies": "18580608011",
  }
  language_dict = {
    "English": "18685580011",
    "Spanish": "18685581011",
    "French": "18685582011",
  }
  params = {
    "audible_programs": main_category_dict.get(main_category, ""),
    "author_author": author_author,
    "keywords": keywords,
    "narrator": narrator,
    "pageSize": pageSize,
    "publisher": publisher,
    "sort": sort,
    "title": title,
    "node": genre_dict.get(genre, ""),
    "feature_six_browse-bin": language_dict.get(language, ""), 
    "ref": f"a_search_l1_audible_programs_{language_dict.get(language, '0')[-2:]}", 
    "pf_rd_p": "daf0f1c8-2865-4989-87fb-15115ba5a6d2",
    "pf_rd_r": "3CSM3Q3AG46QRQ0TVK0F",
    "pageLoadId": "dELu6hUurPGV8fAu",
    "creativeId": "9648f6bf-4f29-4fb4-9489-33163c0bb63e"
  }
  if page > 1:
    params["page"] = page
  query = "&".join([f"{key}={value}" for key, value in params.items()])
  return base_url + query


def string_to_date(text):
    '''
    Convert string to date object
    datetime.date
        year in float
        ex: 2013.2993150684931
    '''
    if text == None:
        return None
    elif 'Release date: ' in text:
        month, day, year = text.split('Release date: ')[1].split('-')
        year = "20"+year
        date =  datetime.date(int(year), int(month), int(day))
        return date.year+ date.month/12 + date.day/365
    elif text.isnumeric():
        return text

def extract_rating(string):
    if string == "Not rated yet" or string == None:
        return None, None
    string = string.split(' out of 5 stars ')
    rating = float(string[0])
    votes = int(string[1].split(' rating')[0].replace(',',''))
    return rating, votes
def hour_min_to_min(tim):
    if tim == None:
        return None
    elif 'min' not in tim:
        return int(tim.split('Length: ')[1].split(' hr')[0])*60
    elif 'hr' not in tim:
        return int(tim.split('Length: ')[1].split(' min')[0])
    else:
        hr = tim.split('Length: ')[1].split(' hr')[0]
        minute = tim.split("and ")[1].split(' min')[0]
    return int(hr)*60 + int(minute)

def scrape_all_details(page):
  response = requests.get(page)
  soup = BeautifulSoup(response.content, "html.parser")
  products = soup.find_all("div", class_="bc-col-responsive bc-col-6")
  details_list = []

  img_tags = soup.find_all("img")
  urls = []
  for i, img_tag in enumerate(img_tags):
    try:
      src = img_tag["src"]
      urls.append(src)

    except:
      src = None
      urls.append(src)
  cover_image = []
  for image_link in urls:
    if "https://m.media-amazon.com/images/I" in image_link or ".jpg" in image_link:
      cover_image.append(image_link)
  if len(cover_image) % 10 != 0:
    print(f"found {len(cover_image)} images found must be the last page or and error occured")
  else:
    print(f"Success: {len(cover_image)} images found")

  for product in products:
    try:
      title = product.find("h3", class_="bc-heading").text.strip()
    except AttributeError:
      title = None
      continue
    try:
      subtitle = product.find("li", class_="bc-list-item subtitle").text.strip()
    except AttributeError:
      subtitle = None
    try:
      author = product.find("li", class_="authorLabel").text.strip()
    except AttributeError:
      author = None
    try:
      narrator = product.find("li", class_="narratorLabel").text.strip()
    except AttributeError:
      narrator = None
    try:
      series = product.find("li", class_="seriesLabel").text.strip()
    except AttributeError:
      series = None
    try:
      length = product.find("li", class_="runtimeLabel").text.strip()
    except AttributeError:
      length = None
    try:
      release_date = product.find("li", class_="releaseDateLabel").text.strip() 
    except AttributeError:
      release_date = None
    try:
      language = product.find("li", class_="languageLabel").text.strip()
    except AttributeError:
      language = None

    try:
      ratings = product.find("li", class_="ratingsLabel").text.strip()
    except AttributeError:
      ratings = None
    try:
      summary = product.find("p", class_="bc-text").text.strip()
    except AttributeError:
      summary = None

    image = None

    try:
      link = product.find("a", class_="bc-link bc-color-link").get("href")
    except AttributeError:
      link = None
    details_dict = {
      "title"        : title,
      "subtitle"     : subtitle,
      "author"       : author,
      "narrator"     : narrator,
      "series"       : series,
      "length"       : length,
      "release_date" : release_date,
      "language"     : language,
      "ratings"      : ratings,
      "vote"         : None,
      "summary"      : summary,
      "image"        : image, 
      "link"         : link 
    }

    for key, value in details_dict.items():
      if value is None: continue
      value = value.strip()
      value = re.sub("\s+", " ", value)
      details_dict[key] = value
    details_list.append(details_dict)
    try:
      details_dict['series'] = details_dict['series'].split('Series: ')[1]
    except:
      details_dict['series'] = None
    try:
      details_dict['author'] = details_dict['author'].split('By: ')[1]
    except:
      details_dict['author'] = None
    try:
      details_dict['narrator'] = details_dict['narrator'].split("Narrated by: ")[1]
    except:
      details_dict['narrator'] = None
    details_dict['length'] = hour_min_to_min(details_dict['length'])
    try:
      details_dict['language'] = details_dict['language'].split('Language: ')[1]
    except:
      details_dict['language'] = None
    details_dict['votes'] = extract_rating(details_dict['ratings'])[1]
    details_dict['ratings'] = extract_rating(details_dict['ratings'])[0]
    details_dict['release_date'] = string_to_date(details_dict['release_date'])
  for i in range(len(details_list)):
    details_list[i]["image"] = cover_image[i]
  return details_list
class AudibleDB:
    def create_db(self):
        self.conn = sqlite3.connect("audible.db")
        self.cur = self.conn.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS audiobooks (
                        title TEXT,
                        subtitle TEXT,
                        author TEXT,
                        narrator TEXT,
                        series TEXT,
                        length INTEGER,
                        release_date TEXT,
                        language TEXT,
                        summary TEXT,
                        image TEXT,
                        link TEXT PRIMARY KEY,
                        ratings REAL,
                        votes INTEGER
                    )
                    """)
        self.conn.commit()
    def insert_data(self, data):
        for item in data:
            title = item["title"]
            subtitle = item["subtitle"]
            author = item["author"]
            narrator = item["narrator"]
            series = item["series"]
            length = item["length"]
            release_date = item["release_date"]
            language = item["language"]
            summary = item["summary"]
            image = item["image"]
            link = item["link"]
            ratings = item["ratings"]
            votes = item["votes"]
            self.cur.execute("""INSERT OR IGNORE INTO audiobooks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                                ON CONFLICT(link) DO NOTHING;
                                """,
                             (title, subtitle, author, narrator, series, length, release_date, language, summary, image, link, ratings, votes))
            if self.cur.rowcount != 0:
                print(title)
        self.conn.commit()

    def read_data(self, **kwargs):
        query = "SELECT * FROM audiobooks WHERE 1=1"
        params = []
        if kwargs.get("author"):
            query += " AND author=?"
            params.append(kwargs["author"])
        if kwargs.get("narrator"):
            query += " AND narrator=?"
            params.append(kwargs["narrator"])
        if kwargs.get("series"):
            query += " AND series=?"
            params.append(kwargs["series"])
        if kwargs.get("language"):
            query += " AND language=?"
            params.append(kwargs["language"])
        if kwargs.get("min_length"):
            query += " AND length>=?"
            params.append(kwargs["min_length"])
        if kwargs.get("min_rating"):
            query += " AND ratings>=?"
            params.append(kwargs["min_rating"])
        if kwargs.get("min_votes"):
            query += " AND votes>=?"
            params.append(kwargs["min_votes"])
        if kwargs.get("search"):
            search_terms = kwargs["search"].split()
            for term in search_terms:
                query += " AND (title LIKE ? OR subtitle LIKE ? OR author LIKE ? OR narrator LIKE ? OR summary LIKE ?)"
                params.extend(["%{}%".format(term)] * 5)
        sort_by = kwargs.get("sort_by", "title")
        sort_order = kwargs.get("sort_order", "ASC")
        query += " ORDER BY {} {}".format(sort_by, sort_order)
        self.cur.execute(query, params)
        results = self.cur.fetchall()
        return results
    def close_db(self):
        self.conn.close()

genre_dict = {
  "Science Fiction": "18580606011",
  "Fantasy": "18580607011",
  "Sci-Fi & Fantasy Anthologies": "18580608011",
  "Arts & Entertainment": "18571910011",
  "Music": "18571942011",
  "Art": "18571913011",
  "Entertainment & Performing Arts": "18571923011",
  "Computers & Technology": "18573211011",
  "Education & Learning": "18573267011",
  "Education": "18573268011",
  "Erotica": "18573351011",
  "Comedy & Humor": "24427740011",
  "Literature & Fiction": "18574426011",
  "Genre Fiction": "18574456011",
  "Psychological": "18574475011",
  "Coming of Age": "18574461011",
  "Biographies & Memoirs": "18571951011",
  "True Crime": "18572017011",
  "Adventurers, Explorers & Survival": "18571952011",
  "Professionals & Academics": "18572005011",
  "Teen & Young Adult": "18580715011",
  "Romance": "18581004011",
  "Money & Finance": "18574547011",
  "Mystery, Thriller & Suspense": "18574597011",
  "Relationships, Parenting & Personal Development": "18574784011"
}

def Romance(page, num=1):
  if num == 1: 
    genre = "Romance"
    return  f"https://www.audible.com/search?audible_programs=20956260011&author_author=&feature_six_browse-bin=18685580011&keywords=&narrator=&node=18580518011&pageSize=50&publisher=&sort=review-rank&title=&page={page}&ref=a_search_c4_pageNum_1&pf_rd_p=1d79b443-2f1d-43a3-b1dc-31a2cd242566&pf_rd_r=3GZFCRJHPG11J59H39ZN&pageLoadId=M2BR61OaYlu76sSQ&creativeId=18cc2d83-2aa9-46ca-8a02-1d1cc7052e2a"
if __name__ == "__main__":
    start_page = 2
    end_page = 10
    db = AudibleDB()
    db.create_db()
    while start_page <= end_page:
        sort ="review-rank" "Popular", "Relevance", "Newest Arrivals", "Customer Rating", "Price - Low to High", "Price - High to Low", "Featured", "Avg. Customer Review"
        link = generate_link(page=start_page, narrator="", sort="review-rank", genre="Romance")
        print(link)
        data = scrape_all_details(link)
        db.insert_data(data)
        start_page += 1
        time.sleep(3)
    db.close_db()