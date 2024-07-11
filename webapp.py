from flask import Flask, render_template, request
import pandas as pd
import sqlite3
app = Flask(__name__)
database_location = r"C:\Users\saket\Documents\GitHub\Pyhton\web scraping\audible.db"
database_location = r"audible.db"
class AudibleDB:
    def create_db(self):
        self.conn = sqlite3.connect(database_location)
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

db = AudibleDB()
db.create_db()
lis = db.read_data()

df = pd.DataFrame(lis, columns=['title', 'subtitle', 'author', 'narrator', 'series', 'length', 'release_date', 'language', 'summary', 'image_url', 'link', 'rating', 'votes'])

df['year'] = df['release_date'].str.split('.').str[0]

def get_input():
    print('enter a test score below')
    user_in = input()
    if not user_in or not user_in.isdigit(): 
        print('error, you must enter a numeric value.')
        return get_input()
    elif len(user_in) > 2: 
        print('error, you can only enter a 2 digit number.')
        return get_input()
    else:
        return user_in
@app.route('/')
def home():
    search = request.args.get('search')
    sort_by = request.args.get('sort_by')
    author = request.args.get('author')
    narrator = request.args.get('narrator')
    series = request.args.get('series')
    language = request.args.get('language')
    min_length = request.args.get('min_length', 0)
    min_rating = request.args.get('min_rating', 0)
    min_votes = request.args.get('min_votes', 0)
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100, type=int)
    try:
        min_length = int(min_length)
    except ValueError:
        min_length = 0
    try:
        min_rating = float(min_rating)
    except ValueError:
        min_rating = 0
    try:
        min_votes = int(min_votes)
    except ValueError:
        min_votes = 0
    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search) | 
                                  filtered_df['author'].str.contains(search) |
                                  filtered_df['narrator'].str.contains(search) |
                                  filtered_df['series'].str.contains(search) |
                                  filtered_df['language'].str.contains(search)]

    if sort_by:
        if sort_by == 'votes':
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)
        else:
            filtered_df = filtered_df.sort_values(by=sort_by)
    if author:
        filtered_df = filtered_df[filtered_df['author'] == author]
    if narrator:
        filtered_df = filtered_df[filtered_df['narrator'] == narrator]
    if series:
        filtered_df = filtered_df[filtered_df['series'] == series]
    if language:
        filtered_df = filtered_df[filtered_df['language'] == language]
    filtered_df = filtered_df[filtered_df['length'] >= int(min_length)]

    if min_rating:
        filtered_df = filtered_df[filtered_df['rating'] >= float(min_rating)]
    if min_votes:
        filtered_df = filtered_df[filtered_df['votes'] >= int(min_votes)]
    paginated_df = filtered_df.iloc[(page-1)*per_page:page*per_page]
    data = paginated_df.to_dict(orient='records')
    return render_template('index.html', data=data, df=df, search=search, author=author, narrator=narrator, series=series, language=language, min_length=min_length, min_rating=min_rating, min_votes=min_votes, page=page, per_page=per_page, sort_by=sort_by)
if __name__ == '__main__':
    app.run(debug=True)
    
