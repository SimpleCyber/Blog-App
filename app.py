from flask import Flask, render_template, request, redirect , url_for
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# initialise firebase 🔥🔥🔥🔥
cred = credentials.Certificate("./firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()



# set th upload  folder and allowed image extension
app.config['UPLOAD_FOLDER'] ='static/uploads'
app.config['ALLOWED_EXTENSIONS'] ={'png','jpg','jpeg','gif','webp'}


    # # Sample blog posts
    # posts = [
    #     {"id":1, "title" : "My first blog post ", "content" : "This is my first post", "image":None},
    #     {"id":2, "title" : "My second blog post ", "content" : "This is my second post", "image":None},

    # ]

def allowed_file(filename):
    """Check th file has the valid extension"""
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']




@app.route("/")
def home():
    post_ref = db.collection("posts").stream()
    posts = []
    tags_count = {}
    for doc in post_ref:
        post = doc.to_dict()
        post["id"] = doc.id
        # tags
        for tag in post.get("tags",[]):
            tags_count[tag] = tags_count.get(tag, 0) + 1

        posts.append(post)
    return render_template("home.html", posts=posts, tags_count = tags_count)


# add posts
@app.route("/add", methods=["GET", "POST"])
def add_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        tags = request.form["tags"].split(",")
        tags = [tag.strip() for tag in tags]

        # handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                image_filename = os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
                file.save(image_filename)

        # add to fire store
        db.collection("posts").add({
            "title" :title ,  
            "content" : content,
            "image": image_filename,
            "tags" : tags,
        })

        return redirect(url_for("home"))
    return render_template("add_post.html")


#delete a post
@app.route("/delete/<string:post_id>")
def delete_post(post_id):
    # delete from firestore
    try:
        db.collection("posts").document(post_id).delete()
        return redirect(url_for("home"))
    except Exception as e:
        print(f"Error deleting post :{e}")
        return redirect(url_for("home"))
        
# update a post
@app.route("/edit/<post_id>", methods=["GET","POST"])
def edit_post (post_id):
    # find post to edit
    post_doc = db.collection("posts").document(post_id)
    post = post_doc.get()
    if not post.exists:
        return redirect(url_for("home"))
    
    post_data = post.to_dict()
    
    if request.method =="POST":
        # update the post with new data
        updated_data = {
            "title" : request.form["title"],
            "content" :request.form["content"],
        }

        
        
        # handle the image upload 
        if 'image' in request.files:
            file =request.files['image']
            if file and allowed_file(file.filename):
                #save image to static folder
                image_filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],image_filename))
                updated_data["image"] = image_filename
            

        post_doc.update(updated_data)
        return redirect(url_for("home"))
    
    return render_template("edit_post.html", post ={"id" :post_id, **post_data})


# search with tags
@app.route  ("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").lower()
    posts_ref = db.collection("posts").stream()
    results = []
    for doc in posts_ref:
        post =doc.to_dict()
        post["id"] = doc.id

        #search in title content tags
        if query in post["title"].lower() or query in post["content"].lower() or query in [tag.lower() for tag in post.get("tags",[])]:
            results.append(post)

    return render_template("search_results.html", query=query, post=results)

if __name__ == "__main__":
    app.run(debug=True) 