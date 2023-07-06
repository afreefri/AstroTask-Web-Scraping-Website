from flask import Flask, render_template, request, session, url_for, redirect
import hashlib  # to hash passwords
from bs4 import BeautifulSoup  # for web scraping
import requests  # also for web scraping
from datetime import datetime


# Initialize the app from Flask
app = Flask(__name__)


@app.route("/")
def index():
    # For now, we save a database in session
    # { userName: [password, zodiac, zip_code, taskArr[]],  user2:[] }
    # db is a dictionary with key username
    # the value is a list containing user information
    # taskArr is a list of user's tasks they have to complete
    if "username" in session:  # if logged in, display the user homepage
        return redirect(url_for("homepage"))

    if "db" not in session:
        session["db"] = {}
    return render_template("user_info.html")


@app.route("/loginAuth", methods=["GET", "POST"])
def loginAuth():
    username = request.form["username"]
    zip_code = request.form["zip_code"]
    zodiac = request.form["zodiac"]
    password = request.form["password"]
    password = hashlib.md5(password.encode()).hexdigest()

    db = session["db"]

    if username in db:
        if db[username][0] != password:
            error = "Username and password do not match! If you are creating a new account, this username is already taken. Try another."
            return render_template("user_info.html", error=error)
        # this means they have logged in before
        if db[username][2] != zip_code:  # if they insert a diff zip, update it
            db[username][2] = zip_code
    else:  # new account, add to db
        db[username] = [password, zodiac, zip_code, []]

    session["username"] = username
    session["db"] = db

    return redirect(url_for("homepage"))


@app.route("/homepage")
def homepage():
    userInfo = session["db"][session["username"]]
    # Get current date
    current_datetime = datetime.now()
    date = current_datetime.strftime("%B %d, %Y")

    # daily horoscope
    user_sign = userInfo[1]
    horoscope_url = "https://www.astrology.com/horoscope/daily/" + user_sign + ".html"
    horoscope_html = requests.get(horoscope_url).text
    #   retrieves the html text of a website
    horoscope_soup = BeautifulSoup(horoscope_html, "lxml")
    #   beautifulsoup instance with out html text and a parser called 'lxml'. This will be
    #   used to parse the text
    horoscope = horoscope_soup.find_all("p")[1].text
    #   retrieve the second paragraph from the website (which is the horoscope). We only want the text, not all the formatting

    # weather and moon phase
    user_zip_code = userInfo[2]
    url = "https://weather.com/weather/today/l/" + user_zip_code
    weather_html = requests.get(url).text
    weather_soup = BeautifulSoup(weather_html, "lxml")
    weather_card = weather_soup.find_all(
        "section", class_="card Card--card--2AzRg Card--containerQuery--T7772"
    )
    location = weather_card[2].h2.text
    location = location.replace("Today's Forecast for ", "")
    temp = weather_soup.find(
        "span", class_="TodayDetailsCard--feelsLikeTempValue--2icPt"
    ).text
    weather = weather_soup.find(
        "div", class_="CurrentConditions--phraseValue--mZC_p"
    ).text
    moon_phase = weather_soup.find_all(
        "div", class_="WeatherDetailsListItem--wxData--kK35q"
    )[7].text

    # quote of the day
    url = "https://altl.io/"
    quote_html = requests.get(url).text
    quote_soup = BeautifulSoup(quote_html, "lxml")
    quote = quote_soup.find("h1", class_="cover-heading").text
    author = quote_soup.find("p", class_="lead").text

    # top cnn headlines and links
    url = "https://www.cnn.com/"
    cnn_html = requests.get(url).text
    cnn_soup = BeautifulSoup(cnn_html, "lxml")
    headlines = cnn_soup.find_all(
        "a",
        class_="container__link container_ribbon__link container_ribbon__left container_ribbon__light",
    )
    news = []
    for story in headlines:
        link = story["href"]
        if "https" not in link:
            link = "https://www.cnn.com/" + link
        title = story.find(attrs={"data-editable": "headline"}).text
        news.append([title, link])
    news.pop()  # get rid of the podcast

    tasks = userInfo[3]

    return render_template(
        "homepage.html",
        username=session["username"],
        date=date,
        temp=temp,
        horoscopeURL=horoscope_url,
        moon_phase=moon_phase,
        horoscope=horoscope,
        location=location,
        weather=weather,
        quote=quote,
        author=author,
        tasks=tasks,  # list of tasks
        headlines=news,  # [[headline, link], [headline, link], ...]
    )


@app.route("/addTasks", methods=["GET", "POST"])
def addTasks():
    # get the tasks from the form and split it into a list called 'tasks'
    taskStr = request.form["tasks"]
    taskStr = taskStr.replace("\r", "")
    tasks = taskStr.split("\n")

    username = session["username"]
    db = session["db"]
    userInfo = db[username]
    taskList = userInfo[3]

    for task in tasks:
        taskList.append(task)

    db[username][3] = taskList
    session["db"] = db

    return redirect(url_for("homepage"))


@app.route("/deleteTasks", methods=["GET", "POST"])
def deleteTasks():
    # get the indices from the form and split it into a list called 'indices'
    idxStr = request.form["indices"]
    idxStr = idxStr.replace("\r", "")
    indices = set(map(int, idxStr.split("\n")))
    # a set of ints representing the indices to be deleted

    username = session["username"]
    db = session["db"]
    userInfo = db[username]
    taskList = userInfo[3]

    newList = [taskList[i] for i in range(len(taskList)) if (i + 1) not in indices]

    db[username][3] = newList
    session["db"] = db

    return redirect(url_for("homepage"))


@app.route("/logout")
def logout():
    # clear everything in the session when you log out
    print(session)
    for key in list(session.keys()):
        # we want to keep the database with the userinfo, so don't delete that
        if key != "db":
            session.pop(key)
    return redirect("/")


app.secret_key = "some key that you will never guess"
if __name__ == "__main__":
    app.run("127.0.0.1", 5000, debug=True)
