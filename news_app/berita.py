from asyncio.windows_events import NULL
from enum import unique
from unicodedata import category
import datetime
from datetime import date
from wsgiref import validate
from flask import Flask, session, render_template, request, redirect, flash, jsonify
from flask_mongoengine import MongoEngine
from flask_mongoengine.wtf import model_form

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost/blog'
}
app.config['SECRET_KEY'] = "b'\x8ekM\x1a\xe0\r\x1e\xf4o0\xa8\x05'"
db = MongoEngine(app)

# Dokumen
#----------------------------------------------------------------------------------------------------------------------
class News(db.Document):
    _id = db.IntField(primary_key=True)
    judul = db.StringField()
    kategori = db.StringField()
    tag = db.ListField(db.StringField())
    tanggal = db.StringField()
    penulis = db.StringField()
    isi = db.StringField()
    click = db.IntField()

class User(db.Document):
    username = db.StringField(unique=True)
    password = db.StringField()

class Categories(db.Document):
    kategori = db.StringField(unique=True)

Newsform = model_form(News)

logged_in = False
# Pipeline
#----------------------------------------------------------------------------------------------------------------------
pipeline = [
    {
        "$group" : { "_id" : "$kategori"}
    }
    ]

pipeline2 = [
    {"$unwind" : "$tag"},
    {
        "$group" : { "_id" : "$tag", "Jumlah" : {"$sum" : 1}}
    },
    {"$sort" : {"Jumlah" : -1}},
    {"$limit" : 10},
]
pipeline3 = [
    {
        "$group" : { "_id" : { 
        "$year" : { 
            "$dateFromString": { "dateString" : "$tanggal", "format": "%Y-%m-%d" } 
        } 
    }
    }},
    {"$sort" : {"_id" : -1}}
]
pipeline4 = [
    {"$project" : {
        "tahun_buat" : {
            "$year" : "$tanggal"},
        "bulan_buat" : {"$month" : "$tanggal"}}},
]
pipeline5 = [
    {
        "$group" : { "_id" : "$penulis"}
    }
    ]
pipeline6 = [
    {
        "$group" : { "_id" : "$username"}
    }
    ]
pipeline7 = [
    {
        "$group" : { "_id" : "$kategori"}
    }
    ]

# Fungsi Berita
#----------------------------------------------------------------------------------------------------------------------
@app.route('/')
def home():
   page = int(request.args.get('page',1))
   limit = int(request.args.get('limit',5))
   total = int(News.objects.count())
   category = News.objects().aggregate(pipeline)
   tahun = News.objects().aggregate(pipeline3)
   penanda = News.objects().aggregate(pipeline2) 
   top = News.objects[:5].order_by('-click')
   top3 = News.objects[:5].order_by('-tanggal')
   data = News.objects().order_by('-tanggal').paginate(page=page, per_page=limit)
   return render_template('index.html', data=data, total=total, category=category, penanda=penanda, tahun=tahun, top=top, top3=top3)

@app.route('/news/<nomor>')
def home2(nomor):
   page = int(request.args.get('page',nomor))
   limit = int(request.args.get('limit',5))
   total = int(News.objects.count())
   category = News.objects().aggregate(pipeline)
   tahun = News.objects().aggregate(pipeline3)
   penanda = News.objects().aggregate(pipeline2) 
   top = News.objects[:5].order_by('-click')
   top3 = News.objects[:5].order_by('-tanggal')
   data = News.objects().order_by('-tanggal').paginate(page=page, per_page=limit)
   return render_template('index.html', data=data, total=total, category=category, penanda=penanda, tahun=tahun, top=top, top3=top3)

@app.route('/kategori/<jenis>/<nomor>')
def search_kategori(jenis, nomor):
   page = int(request.args.get('page', nomor))
   limit = int(request.args.get('limit',5))
   total = int(News.objects.count())
   choice = News.objects(kategori=jenis).first()
   tahun = News.objects().aggregate(pipeline3)
   penanda = News.objects().aggregate(pipeline2) 
   top = News.objects[:5].order_by('-click')
   top3 = News.objects[:5].order_by('-tanggal')
   category = News.objects().aggregate(pipeline)
   data = News.objects(kategori=jenis).order_by('-tanggal').paginate(page=page, per_page=limit)
   return render_template('search.html', data=data, total=total, category=category, choice=choice, penanda=penanda, tahun=tahun, top=top, top3=top3)

@app.route('/tag/<jenis>/<nomor>')
def search_tag(jenis, nomor):
   page = int(request.args.get('page', nomor))
   limit = int(request.args.get('limit',5))
   total = int(News.objects.count())
   choice = jenis
   penanda = News.objects().aggregate(pipeline2)
   tahun = News.objects().aggregate(pipeline3) 
   top = News.objects[:5].order_by('-click')
   top3 = News.objects[:5].order_by('-tanggal')
   category = News.objects().aggregate(pipeline)
   data = News.objects(tag__in=[jenis]).paginate(page=page, per_page=limit)
   return render_template('tag.html', data=data, total=total, category=category, choice=choice, tahun=tahun, penanda=penanda, top=top, top3=top3)

@app.route('/sort/<tahun>/<bulan>')
def search_time(tahun, bulan):
   total = int(News.objects.count())
   tanggal2 = "%s-%s-01" % (tahun,str(int(bulan)+1).zfill(2))
   tanggal2_1 = "%s-%s-01" % (tahun,str(int(bulan)).zfill(2))
   penanda = News.objects().aggregate(pipeline2)  
   category = News.objects().aggregate(pipeline)
   tahun = News.objects().aggregate(pipeline3) 
   top = News.objects[:5].order_by('-click')
   top3 = News.objects[:5].order_by('-tanggal')
   data = News.objects(tanggal__gte = tanggal2_1, tanggal__lt = tanggal2).order_by('-tanggal')
   return render_template('sort.html', data=data, total=total, category=category, tahun=tahun, penanda=penanda, bulan=bulan, top=top, top3=top3)

@app.route('/detail_berita/<id>')
def detail(id):
    data = News.objects(_id = id).first()
    click = int(data.click)+1
    post = News.objects(_id=id).update(
            set__click = click,
    )
    total = int(News.objects.count())
    category = News.objects().aggregate(pipeline)
    top = News.objects[:5].order_by('-click')
    top3 = News.objects[:5].order_by('-tanggal')
    tahun = News.objects().aggregate(pipeline3)
    penanda = News.objects().aggregate(pipeline2) 
    return render_template('post-details.html', data=data, category=category, tahun=tahun, penanda=penanda, top=top, top3=top3)


# Fungsi Admin
#----------------------------------------------------------------------------------------------------------------------

@app.route('/add/<aksi>', methods=['POST'])
def my_form_post(aksi):
    data = News.objects().order_by('-_id').first()
    id = int(data._id)+1
    title = request.form['judul']
    category = request.form['category']
    tag = request.form['tag']
    tag = tag.split(", ")
    date = request.form['date']
    writer = request.form['writer']
    content = request.form['content']
    click = 0
    if aksi == 'new' :
        post = News(_id=id, judul=title, kategori=category, tag=tag, tanggal=date, penulis=writer, isi=content, click=click)
        post.save()
    else :
         post = News.objects(_id=aksi).update(
            set__judul = title,
            set__kategori = category,
            set__tag = tag,
            set__tanggal = date,
            set__penulis =writer,
            set__isi = content,
        )
    return redirect('/admin')

@app.route('/admin/delete/<id>')
def my_form_delete(id):
    data = News.objects(_id=id).first()
    data.delete()
    return redirect('/admin')

@app.route('/admin/addnews')
def my_form_post1():
    if logged_in != True :
        return redirect('/login')
    action = 1
    category = Categories.objects().aggregate(pipeline)
    return render_template('add.html', category=category, action=action)

@app.route('/admin/editnews/<id>')
def my_form_edit(id):
    if logged_in != True :
        return redirect('/login')
    action = 2
    data = News.objects(_id=id).first()
    tags = data.tag
    penanda = ', '.join(map(str, tags))
    category = Categories.objects().aggregate(pipeline)
    return render_template('add.html', data=data, action=action, category=category, penanda=penanda)

@app.route('/admin')
def my_form_post2():
    if logged_in != True :
        return redirect('/login')
    data = News.objects().order_by('-_id')
    user = User.objects().aggregate(pipeline6)
    kategori = Categories.objects().aggregate(pipeline7)
    user_js = []
    kategori_js = []
    for x in user :
        user_js.append(x)
    for x in kategori :
        kategori_js.append(x)
    return render_template('user.html', data=data, user=user_js, kategori=kategori_js)

@app.route('/login')
def my_form_login():
    return render_template('login.html')

@app.route('/logout')
def my_form_logout():
    global logged_in
    logged_in = False
    return redirect('/')

@app.route('/login/check', methods=['POST'])
def check():
    global logged_in
    name = request.form['username']
    user = User.objects(username=name).first()
    if user == None :
        flash('Username tidak ditemukan')
        return redirect('/login')
    password = request.form['password']
    if password != user.password :
        flash('Password salah')
        return redirect('/login')
    logged_in = True
    return redirect('/admin')

@app.route('/adduser', methods=['POST'])
def not_user():
    user = request.form['username']
    password = request.form['password']
    post = User(username=user, password=password)
    post.save()
    return redirect('/admin')

@app.route('/addcategory', methods=['POST'])
def add_category():
    category = request.form['add_kategori']
    post = Categories(kategori=category)
    post.save()
    return redirect('/admin')

if __name__ == '__main__':
   app.run(debug = True)