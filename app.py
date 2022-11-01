from flask import Flask, request, render_template, redirect, session, jsonify
import mysql.connector, mysql.connector.pooling
import os # for secret key

# Define connection arguments in a dictionary
dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "12345678",
    "database": "website",
    "buffered": True # all cursor of cnx are buffered
}
# Create MySQLConnectionPool object for connection pool
cnxpool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name = "website_pool",
    pool_size = 3,
    **dbconfig
)

# Create Application object: "public" folder and "/" path for static files
app = Flask(__name__, static_folder = "public", static_url_path = "/")
app.secret_key = os.urandom(16) # Generate random string for secret key

# Handle route "/" as homepage
@app.route("/")
def index():
    return render_template("index.html")

# Handle "/signup" to sign up
@app.route("/signup", methods = ["POST"])
def signup():
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    try:
        cnx = cnxpool.get_connection()
        cnxcursor = cnx.cursor()
        cnxcursor.execute("SELECT username FROM member WHERE username=%s", (username,))
        check_member_exists = cnxcursor.fetchone()
        if check_member_exists:
            return redirect("/error?message=帳號已經被註冊")
        else:
            cnxcursor.execute("INSERT INTO member(name, username, password) VALUE(%s, %s, %s)", (name, username, password))
            cnx.commit()
            return redirect("/")
    except:
        print("UNSPECTED ERROR.")
    finally:
        cnxcursor.close()
        cnx.close()    

# Handle "/signin" to sign in
@app.route("/signin", methods = ["POST"])
def signin():
    username = request.form.get("username")
    password = request.form.get("password")
    try:
        # Get connection from connection pool
        cnx = cnxpool.get_connection()
        cnxcursor = cnx.cursor(dictionary = True) # Create cursor which return dictionary, default is tuple
        cnxcursor.execute("SELECT id, name, username FROM member WHERE username=%s AND password=%s", (username, password))
        member = cnxcursor.fetchone()
        # If member exists in table "member" in database
        if member:
            # Create session
            session["id"] = member["id"]
            session["name"] = member["name"]
            session["username"] = member["username"]
            return redirect("/member")
        else:
            return redirect("/error?message=帳號或密碼輸入錯誤")
    except:
        print("UNSPECTED ERROR.")
    finally:
        # Close connection
        cnxcursor.close()
        cnx.close()

# Handle "/signout" to sign out
@app.route("/signout")
def signout():
    # Remove session data, sign out
    session.clear()
    return redirect("/")

# Handle route "/member" for member page
@app.route("/member")
def member():
    if "username" in session:
        return render_template("member.html", name = session["name"])
    else:
        return redirect("/")

@app.route("/error")
def error():
    message = request.args.get("message")
    return render_template("error.html", message = message)

# Request-1
# Handle route "api/member" with query string to query the name of member
@app.route("/api/member", methods = ["GET"])
def query_member_name():
    username = request.args.get("username")
    try:
        # Get connection from connection pool
        cnx = cnxpool.get_connection()
        cnxcursor = cnx.cursor(dictionary = True) # Create cursor which return dictionary, default is tuple
        cnxcursor.execute("SELECT id, name, username FROM member WHERE username=%s", (username,))
        member = cnxcursor.fetchone()
        return jsonify({"data": member}) # Return JSON
    except:
        print("UNSPECTED ERROR.")
    finally:
        # Close connection
        cnxcursor.close()
        cnx.close()

# Request-3
# Handle route "api/member" to update the name of member
@app.route("/api/member", methods = ["PATCH"])
def update_member_name():
    # Check if already signed in
    if "username" in session:
        new_name = request.json # Get name from PATCH request
        try:
            # Get connection from connection pool
            cnx = cnxpool.get_connection()
            cnxcursor = cnx.cursor(dictionary = True) # Create cursor which return dictionary, default is tuple
            cnxcursor.execute("UPDATE member SET name=%s WHERE username=%s", (new_name["name"], session["username"]))
            cnx.commit()
            session["name"] = new_name["name"]
            return jsonify({"ok": True}) # Return JSON
        except:
            print("UNSPECTED ERROR.")
        finally:
            # Close connection
            cnxcursor.close()
            cnx.close()
    else:
        return jsonify({"error": True}) # Return JSON

if __name__ == "__main__" :
    app.run(port = 3000)