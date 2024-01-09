import os
import pandas as pd
from PIL import Image, ImageTk
import pyhdfs
from pymongo import InsertOne, MongoClient, UpdateOne, DeleteOne
import shutil
import subprocess
from time import time
import tkinter as tk
from scripts.utils import cache_init, cache_find
import scripts.drop_all

font_sizes = (14, 18, 24, 60, 10)
font_name = "comic sans ms"
FONTS = [[font_name, size] for size in font_sizes]
TITLE_COLOR = '#001168'
MP_COLOR = '#2146FF'
BUTTON_BACKGROUND = '#EDF0FF'


class Article(tk.Tk):  # based on the digitalocean.com/community/tutorials/tkinter-working-with-classes tutorial
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.geometry('800x600+400+300')  # Window size & position
        self.wm_title("Article Application")  # Adding a title to the window

        # creating a frame and assigning it to container
        container = tk.Frame(self)
        # specifying the region where the frame is packed in root
        container.pack(side="top", fill="both", expand=True)

        # configuring the location of the container using grid
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # We will now create a dictionary of frames
        self.frames = {}
        # ...and a list of pages
        pages = (
            MainPage,
            UserPage,
            CreateUserPage,
            EditUserPage,
            DeleteUserPage,
            ArticlePage,
            ReadPage,
            BeReadPage,
            DailyRankPage,
            WeeklyRankPage,
            MonthlyRankPage
        )
        # we'll create the frames themselves later but let's add the components to the dictionary.
        for F in pages:
            frame = F(container, self)

            # the windows class acts as the root window for the frames.
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.client = pyhdfs.HdfsClient(hosts=['localhost:9870'], user_name='dsapo')  

        # Using a method to switch frames
        self.show_frame(MainPage)

    def db(self):  # getting our database
        return MongoClient('localhost', 30000).ddbs

    def show_frame(self, cont):
        frame = self.frames[cont]
        # raises the current frame to the top
        frame.tkraise()

    def create_user(self, user_dict):
        fields = ('uid', 'name', 'gender', 'email', 'phone', 'dept', 'grade', 
                    'language', 'region', 'role', 'preferTags', 'obtainedCredits')
        new_dict = dict(zip(fields, user_dict))
        new_dict['id'] = 'u' + new_dict['uid']
        new_dict['timestamp'] = str(round(time() * 1e3))
        print(new_dict)
        if new_dict['region'] == 'Beijing':
            self.db().region_b.bulk_write([InsertOne(new_dict)])
        elif new_dict['region'] == 'Hong Kong':
            self.db().region_h.bulk_write([InsertOne(new_dict)])

    def edit_user(self, user_dict):
        uid = user_dict['uid']
        del user_dict['uid']
        cache_init().delete(f'user_{uid}')
        self.db().region_b.bulk_write([UpdateOne({'uid': uid}, {'$set': user_dict}, upsert=False)])
        self.db().region_h.bulk_write([UpdateOne({'uid': uid}, {'$set': user_dict}, upsert=False)])

    def delete_user(self, uid):
        cache_init().delete(f"user_{uid}")
        user_dict = {'uid': uid}
        self.db().region_b.bulk_write([DeleteOne(user_dict)])
        self.db().region_h.bulk_write([DeleteOne(user_dict)])

    def get_data(self, id, tklist, attributes, id_name, fields, results, entity, sort=True):
        tklist.delete(0, tk.END) 
        query = {id_name: {'$in': id.split()}}  # todo maybe theres mistake here regarding beread/read 
        found = cache_find(query, {}, id, id_name, entity, attributes)
        results['text'] = f'Found {len(found)} {entity}s.'
        if sort:
            found = sorted(found, key=lambda x: int(x[id_name]))
        for element in found:
            tklist.insert(tk.END, ', '.join([f + ': ' + str(element[f]) for f in fields]))

    def get_user(self, uid, tklist, results):
        self.get_data(uid, tklist, (self.db().region_b, self.db().region_h), 'uid', 
                        ('uid', 'name', 'region', 'gender'), results, 'user')

    def get_article(self, aid, tklist, results, sort=True):
        self.get_data(aid, tklist, (self.db().category_s, self.db().category_t), 'aid', 
                        ('aid', 'title', 'category', 'authors'), results, 'article', sort=sort)

    def get_be_read(self, aid, tklist, results):
        self.get_data(aid, tklist, (self.db().read_cat_s, self.db().read_cat_t), 'aid', 
                        ('aid', 'readNum', 'commentNum', 'agreeNum', 'shareNum'), results, 'be_read')

    def get_ua_au(self, id, id_name, tklist):
        tklist.delete(0, tk.END)
        query = {id_name: id}
        attributes = (self.db().read_b, self.db().read_h)
        found = cache_find(query, {}, id, id_name, 'read', attributes)
        ids = list(map(lambda x: x[chr(-ord(id_name[0]) + ord('a') + ord('u')) + id_name[1:]], # uid->aid, aid->uid
                        found))
        return ids

    def get_article_user(self, uid, tklist, results):
        aids = self.get_ua_au(uid, 'uid', tklist)
        self.get_article(' '.join(aids), tklist, results)

    def get_user_article(self, aid, tklist, results):
        uids = self.get_ua_au(aid, 'aid', tklist)
        self.get_user(' '.join(uids), tklist, results)

    def get_rank(self, date, desc, rank, max_num, tklist, results):
        tklist.delete(0, tk.END)
        query = {'timestamp': date, 'temporalGranularity': desc}
        found = list(rank.find(query, {}))
        results['text'] = f'Found {len(found)} results.' if found else 'Found no results.'
        if found: 
            aids = found[0]['articleAidList']
            self.get_article(' '.join(aids[:max_num]), tklist, results, sort=False)

    def get_daily_rank(self, text, max_num, tklist, results):
        day = str(pd.to_datetime(text, format='%d/%m/%Y').value // 1e6)
        self.get_rank(day, 'daily', self.db().popular_d, max_num, tklist, results)

    def get_weekly_rank(self, text, max_num, tklist, results):
        week = str(pd.to_datetime('0/' + text, format='%w/%W/%Y').value // 1e6)
        self.get_rank(week, 'weekly', self.db().popular_w, max_num, tklist, results)

    def get_monthly_rank(self, text, max_num, tklist, results):
        month = str(pd.to_datetime(text, format='%m/%Y').value // 1e6)
        self.get_rank(month, 'monthly', self.db().popular_m, max_num, tklist, results)

    def kill_all(self):
        exec(open('./scripts/drop_all.py').read()) #drop collectionsC:\Users\dsapo\2023\ddbs
        temp = ''.join(subprocess.getoutput(["docker", "container", "ls", "-q"])).split('\n')
        for container in temp:
            subprocess.run(["docker", "stop", str(container)])

        processes = ''.join(subprocess.getoutput(["docker", "ps", "-a", "-q"])).split('\n')
        for cps in processes:
            subprocess.run(["docker", "rm", "-f", str(cps)])

        volumes = ''.join(subprocess.getoutput(["docker", "volume", "ls", "-q"]) ).split('\n')
        for vol in volumes:
            subprocess.run(["docker", "volume", "rm", str(vol)])

    def open_article(self, articles):  
        article = articles.curselection()
        if article:
            print(articles.get(article[0]).split())
            article = 'article' + articles.get(article[0]).split()[1][:-1]
            articles_path = '/user/dsapo/articles/'
            # articles_path = 'C:/Users/dsapo/2023/ddbs/db-generation/articles/'
            tmp_dir = './tmp/'
            tmp_dir = 'C:/Users/dsapo/2023/ddbs/hadoop-3.3.6/temp'
            # tmp_dir = 'C:/Users/dsapo/2023/ddbs/db-generation/articles/' + article + '/'
            newWindow = tk.Toplevel()
            newWindow.title(article)
            newWindow.geometry("900x630-300-100")
            frame = tk.Frame(newWindow, width=630, height=900)
            frame.pack()
            full_article_path = articles_path + article
            print(full_article_path + '/')
            # files = os.listdir(articles_path + article + '/')
            files = self.client.listdir(full_article_path + '/')
            jpg_files = list(filter(lambda x: x.endswith("jpg"), files))
            txt_file = list(filter(lambda x: x.endswith("txt"), files))[0]
            flv_files = list(filter(lambda x: x.endswith("flv"), files))
            for i, file in enumerate(jpg_files):
                self.client.copy_to_local(full_article_path + '/' + file, tmp_dir + file)
                image = Image.open(tmp_dir + file).resize((100, 178))
                image = ImageTk.PhotoImage(image)
                panel = tk.Label(frame, image=image)
                panel.image = image
                panel.place(x=10, y=40 + 180 * i)
            with self.client.open(full_article_path + '/' + txt_file) as f:
                text = f.read()
            text_box = tk.Text(frame, font=('comic sans ms', 10), height=30, width=58)
            text_box.place(x=160, y=40)
            text_box.insert('end', text)
            for file in flv_files:
                self.client.copy_to_local(full_article_path + '/' + file, tmp_dir + file)
                os.startfile(tmp_dir + file)

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="DDBS Management", font=FONTS[3], fg=TITLE_COLOR, padx=60
                 ).grid(row=0, column=1, columnspan=5)

        tk.Button(self, text="Users", 
                    command=lambda: controller.show_frame(UserPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=1, column=1, columnspan=3, sticky='e')
        tk.Label(self, text="Search and create/edit/delete users by their IDs", 
                 font=FONTS[0], fg='black', padx=20).grid(row=1, column=4, sticky='w')

        tk.Button(self, text="Articles",
                    command=lambda: controller.show_frame(ArticlePage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=2, column=1, columnspan=3, sticky='e')
        tk.Label(self, text="Search and open articles by their IDs", 
                 font=FONTS[0], fg='black', padx=20).grid(row=2, column=4, sticky='w')

        tk.Button(self, text="User-Article Info",
                    command=lambda: controller.show_frame(ReadPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=3, column=1, columnspan=3, sticky='e')
        tk.Label(self, text="Used to search what articles the user read or which users read the article by corresponding IDs (Read)", 
                 font=FONTS[0], fg='black', padx=20, wraplength=500).grid(row=3, column=4, sticky='w')

        tk.Button(self, text="Article Stats",
                    command=lambda: controller.show_frame(BeReadPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=4, column=1, columnspan=3, sticky='e')
        tk.Label(self, text="Information about articles (Be-Read)", 
                 font=FONTS[0], fg='black', padx=20).grid(row=4, column=4, sticky='w')

        tk.Label(self, text="", 
                 font=FONTS[0], fg='black', padx=10).grid(row=5, column=0)
        tk.Button(self, text="Day",
                    command=lambda: controller.show_frame(DailyRankPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=5, column=1)
        tk.Button(self, text="Week",
                    command=lambda: controller.show_frame(WeeklyRankPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=5, column=2)
        tk.Button(self, text="Month",
                    command=lambda: controller.show_frame(MonthlyRankPage), font=FONTS[2], fg=MP_COLOR, background=BUTTON_BACKGROUND).grid(row=5, column=3)
        tk.Label(self, text="Popularity ranks", 
                 font=FONTS[0], fg='black', padx=20).grid(row=5, column=4, sticky='w')
        
        # tk.Button(self, text="KILL",
                    # command=lambda: controller.show_frame(MonthlyRankPage), font=FONTS[2], fg='white', background='red').grid(row=6, column=4, sticky='e')
        tk.Button(self, text="KILL",
                    command=lambda: app.kill_all(), font=FONTS[2], fg='white', background='red').grid(row=6, column=4, sticky='e')



class UserPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Users", font=FONTS[2], fg=TITLE_COLOR)
        label.pack(pady=10, padx=10)

        buttons = tk.Frame(self)
        buttons.pack(pady=5)

        tk.Button(buttons, text="Create",
                    command=lambda: app.show_frame(CreateUserPage), font=FONTS[0], bg=MP_COLOR, background=BUTTON_BACKGROUND).pack(side=tk.LEFT)
        tk.Label(buttons, text="", font=FONTS[0], padx=5).pack(side=tk.LEFT)

        tk.Button(buttons, text="Edit",
                    command=lambda: app.show_frame(EditUserPage), font=FONTS[0], bg=MP_COLOR, background=BUTTON_BACKGROUND).pack(side=tk.LEFT)
        tk.Label(buttons, text="", font=FONTS[0], padx=5).pack(side=tk.LEFT)

        tk.Button(buttons, text="Delete",
                    command=lambda: app.show_frame(DeleteUserPage), font=FONTS[0], bg=MP_COLOR, background=BUTTON_BACKGROUND).pack(side=tk.LEFT)

        top_frame = tk.Frame(self)
        top_frame.pack()

        tk.Label(top_frame, text='User ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        user_text = tk.StringVar()
        tk.Entry(top_frame, textvariable=user_text).pack(side=tk.LEFT)
        tk.Label(top_frame, text="", font=FONTS[0], padx=2).pack(side=tk.LEFT)

        tk.Button(top_frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_user(user_text.get(), result_list, results)).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=20, width=75)
        result_list.pack()

        tk.Button(self, text="To Main Page", font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack()

class CreateUserPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Create User", font=FONTS[2], fg=TITLE_COLOR).grid(row=0, column=1, columnspan=4)

        vars = []
        for i, label in enumerate(('User ID', 'Name', 'Gender', 'Email', 'Phone', 'Department', 
                                    'Grade', 'Language', 'Region', 'Role', 'Tags', 'Credits')):
            if i % 2 == 0:
                tk.Label(self, text='', font=FONTS[0], padx=90).grid(row=1 + i // 2, column=0)
            tk.Label(self, text=label, font=FONTS[0], pady=20, padx=20).grid(row=1 + i // 2, column=1 + i % 2 * 2, sticky='e')
            var = tk.StringVar()
            vars.append(var)
            tk.Entry(self, textvariable=var).grid(row=1 + i // 2, column=2 + i % 2 * 2, sticky='w')

        tk.Button(self, text='Create User', font=FONTS[1], background=BUTTON_BACKGROUND,
                    command=lambda: app.create_user(list(map(lambda x: x.get(), vars))),
                    ).grid(row=7, column=1, columnspan=4)

        tk.Label(self, text='', font=('comic sans ms', 1), pady=0).grid(row=8, column=0)
        tk.Button(self, text="Back", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(UserPage)).grid(row=9, column=1, columnspan=4)

        tk.Button(self, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).grid(row=10, column=1, columnspan=4)


class EditUserPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Edit User", font=FONTS[2], fg=TITLE_COLOR).grid(row=0, column=1, columnspan=4)

        vars = {}

        field_names = ('User ID', 'Name', 'Gender', 'Email', 'Phone', 'Department', 
                        'Grade', 'Language', 'Region', 'Role', 'Tags', 'Credits')
        field_formal = ('uid', 'name', 'gender', 'email', 'phone', 'dept', 
                        'grade', 'language', 'region', 'role', 'preferTags', 'obtainedCredits')

        for i, (name, formal) in enumerate(zip(field_names, field_formal)):
            if i % 2 == 0:
                tk.Label(self, text='', font=FONTS[0], padx=90).grid(row=1 + i // 2, column=0)
            tk.Label(self, text=name, font=FONTS[0], pady=20, padx=20).grid(row=1 + i // 2, column=1 + i % 2 * 2, sticky='e')
            var = tk.StringVar()
            vars[formal] = var
            tk.Entry(self, textvariable=var).grid(row=1 + i // 2, column=2 + i % 2 * 2, sticky='w')

        tk.Button(self, text='Edit User', font=FONTS[1], background=BUTTON_BACKGROUND,
                    command=lambda: app.edit_user(dict(map(lambda x: (x[0], x[1].get()), vars.items()))),
                    ).grid(row=7, column=1, columnspan=4)

        tk.Label(self, text='', font=('comic sans ms', 1), pady=0).grid(row=8, column=0)
        tk.Button(self, text="Back", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(UserPage)).grid(row=9, column=1, columnspan=4)

        tk.Button(self, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).grid(row=10, column=1, columnspan=4)

class DeleteUserPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Delete User", font=FONTS[2], fg=TITLE_COLOR)
        label.pack(pady=10, padx=10)

        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text='User ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)
        user_text = tk.StringVar()
        tk.Entry(frame, textvariable=user_text).pack(side=tk.LEFT)

        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.delete_user(user_text.get()),
                    pady=5, padx=20).pack(side=tk.LEFT)

        back = tk.Frame(self)
        back.pack()
        tk.Button(back, text="Back", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(UserPage)).pack(side=tk.LEFT)

        back = tk.Frame(self)
        back.pack(pady=10)
        tk.Button(back, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack(side=tk.LEFT)

class ArticlePage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Articles", font=FONTS[2], fg=TITLE_COLOR)
        label.pack()

        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text='Article ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        article_text = tk.StringVar()
        tk.Entry(frame, textvariable=article_text).pack(side=tk.LEFT)

        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_article(article_text.get(), result_list, results),
                    ).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=20, width=75)
        result_list.pack()

        result_list.bind('<Double-1>', lambda x: app.open_article(result_list))

        buttons = tk.Frame(self)
        buttons.pack(pady=10)
        tk.Button(self, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack()

class ReadPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Reads", font=FONTS[2], fg=TITLE_COLOR)
        label.pack(pady=10, padx=10)

        frame1 = tk.Frame(self)
        frame1.pack()
        tk.Label(frame1, text='User ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        text1 = tk.StringVar()
        tk.Entry(frame1, textvariable=text1).pack(side=tk.LEFT)

        tk.Button(frame1, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_article_user(text1.get(), result_list1, results1),
                    pady=5, padx=20).pack(side=tk.LEFT)
        frame2 = tk.Frame(self)
        frame2.pack()
        tk.Label(frame1, text='Article ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        results1 = tk.Label(self, text='', font=FONTS[0], padx=20)
        results1.pack()

        result_list1 = tk.Listbox(self, height=20, width=75)
        result_list1.pack()

        text2 = tk.StringVar()
        tk.Entry(frame1, textvariable=text2).pack(side=tk.LEFT)

        tk.Button(frame1, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_user_article(text2.get(), result_list1, results1),
                    pady=5, padx=20).pack(side=tk.LEFT)

        tk.Button(self, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack(pady=30)


class BeReadPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Be Read", font=FONTS[2], fg=TITLE_COLOR).pack(pady=10, padx=10) # 

        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text='Article ID', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        article_text = tk.StringVar()
        tk.Entry(frame, textvariable=article_text).pack(side=tk.LEFT)

        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_be_read(article_text.get(), result_list, results),
                    pady=5, padx=20).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=20, width=75)
        result_list.pack()

        tk.Button(self, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack(side=tk.BOTTOM, pady=30)


class DailyRankPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Daily Rank", font=FONTS[2], fg=TITLE_COLOR).pack(pady=10, padx=10)

        frame = tk.Frame(self)
        frame.pack()
        tk.Label(frame, text='Format is day/month/year, ex. 1/1/2018', font=FONTS[0]).pack(side=tk.LEFT)

        frame = tk.Frame(self)
        frame.pack(pady=10)

        tk.Label(frame, text='Day', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        day = tk.StringVar()
        tk.Entry(frame, textvariable=day).pack(side=tk.LEFT)
        tk.Label(frame, text='Max', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        max_num = tk.StringVar()
        e = tk.Entry(frame, textvariable=max_num)
        e.pack(side=tk.LEFT)
        e.insert(tk.END, '5')
        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_daily_rank(day.get(), int(max_num.get()), result_list, results),
                    pady=5, padx=20).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=15, width=75)
        result_list.pack()

        back = tk.Frame(self)
        back.pack(pady=10)

        tk.Button(back, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack(side=tk.LEFT)


class WeeklyRankPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Weekly Rank", font=FONTS[2], fg=TITLE_COLOR).pack(pady=10, padx=10)

        frame = tk.Frame(self)
        frame.pack()
        tk.Label(frame, text='Format is week/year, ex. 1/2018', font=FONTS[0]).pack(side=tk.LEFT)

        frame = tk.Frame(self)
        frame.pack()

        tk.Label(frame, text='Week', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)
        week = tk.StringVar()
        tk.Entry(frame, textvariable=week).pack(side=tk.LEFT)

        tk.Label(frame, text='Max', font=FONTS[0], pady=20, padx=20).pack(side=tk.LEFT)

        max_num = tk.StringVar()
        e = tk.Entry(frame, textvariable=max_num)
        e.pack(side=tk.LEFT)
        e.insert(tk.END, '5')

        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: app.get_weekly_rank(week.get(), int(max_num.get()), result_list, results),
                    pady=5, padx=20).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=15, width=75)
        result_list.pack()

        back = tk.Frame(self)
        back.pack(pady=10)

        tk.Button(back, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: app.show_frame(MainPage)).pack(side=tk.LEFT)


class MonthlyRankPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Monthly Rank", font=FONTS[2], fg=TITLE_COLOR).pack(pady=10, padx=10)

        frame = tk.Frame(self)
        frame.pack()
        tk.Label(frame, text='Format is month/year, ex. 1/2018', font=FONTS[0]).pack(side=tk.LEFT)

        frame = tk.Frame(self)
        frame.pack()

        month_label = tk.Label(frame, text='Month', font=FONTS[0], pady=20, padx=20)
        month_label.pack(side=tk.LEFT)

        month_text = tk.StringVar()
        month_entry = tk.Entry(frame, textvariable=month_text)
        month_entry.pack(side=tk.LEFT)

        top_label = tk.Label(frame, text='Top', font=FONTS[0], pady=20, padx=20)
        top_label.pack(side=tk.LEFT)

        max_num = tk.StringVar()
        e = tk.Entry(frame, textvariable=max_num)
        e.pack(side=tk.LEFT)
        e.insert(tk.END, '5')

        tk.Button(frame, text='submit', font=FONTS[4], background=BUTTON_BACKGROUND,
                    command=lambda: controller.get_monthly_rank(month_text.get(), int(max_num.get()), result_list, results),
                    pady=5, padx=20).pack(side=tk.LEFT)

        results = tk.Label(self, text='', font=FONTS[0], padx=20)
        results.pack()

        result_list = tk.Listbox(self, height=15, width=75)
        result_list.pack()

        back = tk.Frame(self)
        back.pack(pady=10)

        tk.Button(back, text="To Main Page", font=FONTS[0], background=BUTTON_BACKGROUND,
                    command=lambda: controller.show_frame(MainPage)).pack(side=tk.LEFT)


if __name__ == '__main__':
    os.makedirs('./tmp/', exist_ok=True)
    app = Article()
    app.geometry('900x630-300-100')
    app.mainloop()
    if os.path.isdir('./tmp/'):
        shutil.rmtree('./tmp/', ignore_errors=True)
