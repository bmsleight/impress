import web
import os
import sqlite3
import subprocess
import shutil
import zipfile

add_path = '/var/www/python-impress-webpy/'
#add_path = ''

render = web.template.render(add_path + 'templates/', base='base')
render_plain = web.template.render(add_path + 'templates/')
sqldb = add_path + "other/impress.db"

urls = (
    '/', 'list', 
    '/list', 'list', 
    '/new/', 'new_impress', 
    '/summary/(\d+)', 'summary', 
    '/edit/(\d+)', 'edit', 
    '/view/(\d+)', 'edit', 
    '/download/(\d+)', 'edit', 
)
app = web.application(urls, globals())


default_rst = """
==============
My fisrt slide
==============

.. slide::
   :class: first

My second slide
===============

.. slide::

"""

new_impress_form = web.form.Form(
        web.form.Textbox('name', description="Name of Presentation"),
        web.form.Password('password'),
        web.form.Password("password2", description="Repeat password"),
        web.form.Button('New Impress'),
        validators = [
            web.form.Validator("Passwords did't match", lambda i: i.password == i.password2)]
        )

def check_login(f):
    # check for login here
    id_, name, password, rst = impress_records(f.id)[0]
    if f.password == password:
        return True
    else:
        return False

valid_credentials = web.form.Validator("Wrong password", check_login)

edit_impress_form = web.form.Form(
            web.form.Hidden("id", description=""),
            web.form.Textarea('code', web.form.notnull, 
                rows=50, cols=40,
                description="Impress content:", post="Use markdown syntax", value=""),
            web.form.Password('password'),
            web.form.Button('Update Impress'),
            validators=[valid_credentials],
        )


class index:
    def GET(self):
        return "Hello, world!"


class list:
    def GET(self):
        records = impress_records()
        return render.list(records)

class new_impress:
    def GET(self): 
        form = new_impress_form()
        return render.new_impress(form)
    def POST(self): 
        form = new_impress_form()
        if not form.validates(): 
            return render.new_impress(form)
        else:
            conn = sqlite3.connect(sqldb)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO impress (Name,Password,Rst) VALUES (?,?,?)',
                (form['name'].value,form['password'].value, default_rst))
            conn.commit()
            new_id = cursor.lastrowid
            raise web.seeother('../edit/' + str(new_id) )


class summary:
    def GET(self, id):
        records = impress_records(id)
        return render.summary(records)

class edit:
    def GET(self, id):
        id_, name, password, rst = impress_records(id)[0]
        form = edit_impress_form()
        form.code.value = rst
        form.id.value = id
        return render.edit(form)
    def POST(self, id): 
        form = edit_impress_form()
        if not form.validates(): 
            return render.edit(form)
        else:
            conn = sqlite3.connect(sqldb)
            cursor = conn.cursor()
            cursor.execute("UPDATE impress SET Rst=? WHERE Id=?", (form['code'].value, form['id'].value))        
            conn.commit()
            generate_impress(form['id'].value)
            raise web.seeother('../summary/' + str(id) )

def impress_records(dbid=-1):
    conn = sqlite3.connect(sqldb)
    cursor = conn.cursor()
    if dbid == -1:
        cursor.execute('select * from impress ')
    else:
        cursor.execute('select * from impress where Id=?', (dbid,))
    records=cursor.fetchall()
    return records

def generate_impress(dbid):
    path = add_path + 'static/impress/' + dbid
    id_, name, password, rst = impress_records(dbid)[0]

    if not os.path.exists(path):
        os.makedirs(path)
    text_file = open(path + "/index.rst", "w")
    text_file.write(rst)
    text_file.close()

    # I could not get the less ugly way to work. Ho humm
    #  impress ;  mkdir -p html/static/impress/js/ ; cp impress.js html/static/impress/js/ ; #wget https://raw.github.com/bartaz/impress.js/master/js/impress.js ; mv impress.js html/static/impress/js/
    os.chdir(path)
    i = subprocess.Popen(["/usr/local/bin/impress",], shell=True, stdout=subprocess.PIPE)
    i.wait()
    os.chdir("../../../")
    os.makedirs(path + "/html/static/impress/js/")
    shutil.copyfile("static/impress.js", path + "/html/static/impress/js/impress.js")

    os.chdir(path)
    zip = zipfile.ZipFile(name + ".zip", 'w')
    zipdir('./html', zip)
    zip.close()
    os.chdir("../../../")


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root,file))



if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
