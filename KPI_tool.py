import glob
import re
import os
from datetime import datetime, timedelta
import git
from git import GitCommandError
import json

ACN_REPO_PATH = "E:/GitHub/techcontent/"
ACOM_REPO_PATH = "E:/GitHub/azure-content-pr/"

STATUS_LIST = ["Most Fresh","Fresh","State","Abandon", "Unknown"]

class Article:

    LAST_SYNC_DATE = None
    THIS_SYNC_DATE = None
    NEXT_SYNC_DATE = None
    FIRST_CONTENT_REFRESH_DATE = None
    LAST_CONTENT_REFRESH_DATE = None

    NEW_SERVICES = None
    ARTICLE_EXCEPTION = None

    ACOM_ARTICLES = None

    MOSTFRESH = 0
    FRESH = 1
    STATE = 2
    ABANDON = 3

    ACOM_GIT_REPO = git.Git(ACOM_REPO_PATH)
    ACN_GIT_REPO = git.Git(ACN_REPO_PATH)

    def __init__(self, acnfilepath):
        self.acnfilepath = acnfilepath
        path, self.filename = os.path.split(acnfilepath)
        directory, folder  = os.path.split(path)
        self.folder = folder
        relative_path = path[len(ACN_REPO_PATH):]
        self._excpetion_or_not = None
        if self.get_excpetion_or_not():
            self.acomfilepath = None
        else:
            if Article.ACOM_ARTICLES == None:
                self._get_acom_articles()
            self.acomfilepath = Article.ACOM_ARTICLES.get(self.filename.lower())
        self._msdate_in_acn = None
        self._msdate_in_acom = None
        self._wacndate = None
        self._status = None
        self._service = None
        self._no_update_or_not = None
        self._new_article_or_not = None

    def _get_acom_articles(self):
        Article.ACOM_ARTICLES = {}
        for article in glob.iglob(ACOM_REPO_PATH+'articles/**/*.md', recursive=True):
            article = article.replace("\\","/")
            filename = os.path.basename(article)
            if Article.ACOM_ARTICLES.get(filename.lower()):
                print("Warning: "+article+" duplicated.")
            else:
                Article.ACOM_ARTICLES[filename.lower()]=article

    def get_msdate_in_acn(self):
        if self._msdate_in_acn == None:
            self._get_msdate_and_wacndate_in_acn()
        return self._msdate_in_acn

    def get_wacndate(self):
        if self._wacndate == None:
            self._get_msdate_and_wacndate_in_acn()
        return self._wacndate

    def _get_msdate_and_wacndate_in_acn(self):
        file = open(self.acnfilepath, "r", encoding="utf8")
        mdcontent = file.read()
        file.close()
        msdate_match = re.findall("ms\.date=\"([^\"]*)\"", mdcontent)
        wacndate_match = re.findall("wacn\.date=\"([^\"]*)\"", mdcontent)
        if len(msdate_match)>0:
            self._msdate_in_acn = msdate_match[0]
        else:
            self._msdate_in_acn = ""
        if len(wacndate_match)>0:
            self._wacndate = wacndate_match[0]
        else:
            self._wacndate = ""
    
    def get_msdate_in_acom(self):
        if self._msdate_in_acom == None:
            self._get_msdate_in_acom()
        return self._msdate_in_acom 

    def _get_msdate_in_acom(self):
        if self.acomfilepath == None:
            self._msdate_in_acom = ""
        else:
            file = open(self.acomfilepath, "r", encoding="utf8")
            mdcontent = file.read()
            file.close()
            msdate_match = re.findall("ms\.date=\"([^\"]*)\"", mdcontent)
            if len(msdate_match)>0:
                self._msdate_in_acom = msdate_match[0]
            else:
                self._msdate_in_acom = ""

    def get_status(self):
        if self._status == None:
            if Article.LAST_CONTENT_REFRESH_DATE == None:
                self._get_last_content_refresh_date()
            if self.get_wacndate == None:
                self._get_msdate_and_wacndate_in_acn()
            if self.get_wacndate() == "":
                print("Waring: "+self.filename+"'s wacn.date is empty.")
                self._status = 4
            else:
                wacndate = datetime.strptime(self.get_wacndate(), "%m/%d/%Y")
                delta = Article.LAST_CONTENT_REFRESH_DATE - wacndate
                if delta.days < 60:
                    self._status = Article.MOSTFRESH
                elif delta.days < 90:
                    self._status = Article.FRESH
                elif delta.days < 120:
                    self._status = Article.STATE
                else:
                    self._status = Article.ABANDON
        return self._status

    def get_service(self):
        if self._service == None:
            if self.folder == "articles":
                self._service = "others"
            else:
                self._service = self.folder.replace("-"," ")
        return self._service

    def get_removed_or_not(self):
        if self.get_excpetion_or_not():
            return None
        return self.acomfilepath == None

    def get_no_update_or_not(self):
        if self.get_excpetion_or_not():
            return None
        if self._no_update_or_not == None:
            if Article.LAST_SYNC_DATE == None:
                self._get_last_sync_date()
            if self.acomfilepath == None:
                self._no_update_or_not = False
                return self._no_update_or_not
            filepath = self.acomfilepath[len(ACOM_REPO_PATH):]
            try:
                old = Article.ACOM_GIT_REPO.show(Article.LAST_SYNC_DATE.strftime("%m%d%Y")+":"+filepath).replace("\ufeff", "")
            except GitCommandError as e:
                self._no_update_or_not = False
                return self._no_update_or_not
            msdate_match = re.findall("ms\.date=\"([^\"]*)\"", old)
            if len(msdate_match)>0:
                old_msdate = msdate_match[0]
            else:
                old_msdate = ""
            self._no_update_or_not = old_msdate == self.get_msdate_in_acom()
        return self._no_update_or_not

    def get_new_article_for_existing_service_or_not(self):
        if Article.NEW_SERVICES == None:
            file = open("new_services.json","r", encoding="utf8")
            Article.NEW_SERVICES = json.loads(file.read())
            file.close()
        if self._new_article_or_not == None:
            if Article.FIRST_CONTENT_REFRESH_DATE == None:
                self._get_first_content_refresh_date()
            filepath = self.acnfilepath[len(ACN_REPO_PATH):]
            try:
                old = Article.ACN_GIT_REPO.show(Article.FIRST_CONTENT_REFRESH_DATE.strftime("%m%d%Y")+":"+filepath)
                self._new_article_or_not = False
            except GitCommandError as e:
                self._new_article_or_not = True
        return self._new_article_or_not and self.get_service() not in Article.NEW_SERVICES

    def _get_last_content_refresh_date(self):
        if Article.NEXT_SYNC_DATE == None:
            self._get_next_sync_date()
        Article.LAST_CONTENT_REFRESH_DATE = Article.NEXT_SYNC_DATE+timedelta(days=10)

    def _get_first_content_refresh_date(self):
        if Article.THIS_SYNC_DATE == None:
            self._get_this_sync_date()
        Article.FIRST_CONTENT_REFRESH_DATE = Article.THIS_SYNC_DATE+timedelta(days=13)

    def _get_sync_date(self, delta_month):
        today = datetime.today()
        last_month = (today+timedelta(days=3)).month-delta_month
        if last_month <= 0:
            last_month = last_month+12
            first_day_of_the_month = datetime(today.year-1, last_month, 1)
        else:
            first_day_of_the_month = datetime(today.year, last_month , 1)
        weekday =  first_day_of_the_month.weekday()
        if weekday == 0:
            return first_day_of_the_month+timedelta(days=15)
        return first_day_of_the_month+timedelta(days=15+7-weekday)

    def _get_last_sync_date(self):
        Article.LAST_SYNC_DATE = self._get_sync_date(3)

    def _get_this_sync_date(self):
        Article.THIS_SYNC_DATE = self._get_sync_date(2)

    def _get_next_sync_date(self):
        Article.NEXT_SYNC_DATE = self._get_sync_date(1)

    def get_excpetion_or_not(self):
        if Article.ARTICLE_EXCEPTION == None:
            file = open("exception_articles.json","r", encoding="utf8")
            Article.ARTICLE_EXCEPTION = json.loads(file.read())
            file.close()
        if self._excpetion_or_not == None:
            self._excpetion_or_not = self.filename in Article.ARTICLE_EXCEPTION
        return self._excpetion_or_not

    def get_should_update_but_not_update_or_not(self):
        if self.get_msdate_in_acom() == "":
            return None
        else:
            return self.get_msdate_in_acom() != self.get_msdate_in_acn()

if __name__ == '__main__':
    service_stat = {}
    new_article_for_existing_services = 0
    acom_removed_files = 0
    acom_no_updates = 0
    content_refresh = 0
    no_exception = 0
    should_update_but_not_update_or_not = 0
    outfile = open("output.csv", "w", encoding="utf8")
    outfile.write("file name,service,ms.date in Acom,ms.date in Acn,wacn.date,status,no update in Acom,new article for existing services,removed in Acom,should update but not update,exception\n")
    for filename in glob.iglob('E:/GitHub/techcontent/articles/**/*.md', recursive=True):
        filepath = filename.replace("\\", "/")
        print("Proccessing: "+filepath)
        article = Article(filepath)
        if service_stat.get(article.get_service())==None:
            service_stat[article.get_service()] = {STATUS_LIST[0]:0, STATUS_LIST[1]:0, STATUS_LIST[2]:0, STATUS_LIST[3]:0}
        service_stat[article.get_service()][STATUS_LIST[article.get_status()]] += 1
        if article.get_new_article_for_existing_service_or_not():
            new_article_for_existing_services += 1
        if article.get_removed_or_not():
            acom_removed_files += 1
        if article.get_no_update_or_not():
            acom_no_updates += 1
        if not article.get_excpetion_or_not():
            no_exception += 1
        if article.get_should_update_but_not_update_or_not():
            should_update_but_not_update_or_not += 1
        line = article.filename+","+article.get_service()+","+article.get_msdate_in_acom()+","+article.get_msdate_in_acn()+","+article.get_wacndate()+","+STATUS_LIST[article.get_status()]+","+str(article.get_no_update_or_not())+","+str(article.get_new_article_for_existing_service_or_not())+","+str(article.get_removed_or_not())+","+str(article.get_should_update_but_not_update_or_not())+","+str(article.get_excpetion_or_not()) +"\n"
        print(line)
        outfile.write(line)
    conten_refresh = no_exception - should_update_but_not_update_or_not - new_article_for_existing_services - acom_no_updates - acom_removed_files
    total_no_exception_no_new_article_for_existing_services = no_exception - new_article_for_existing_services
    outfile.close()

    outfile = open("output2.csv", "w", encoding="utf8")
    outfile.write(","+STATUS_LIST[0]+","+STATUS_LIST[1]+","+STATUS_LIST[2]+","+STATUS_LIST[3]+"\n")
    for service in sorted(service_stat.keys()):
        outfile.write(service+","+str(service_stat[service][STATUS_LIST[0]])+","+str(service_stat[service][STATUS_LIST[1]])+","+str(service_stat[service][STATUS_LIST[2]])+","+str(service_stat[service][STATUS_LIST[3]])+"\n")

    outfile.write(",,,,\n")
    outfile.write(",,,,\n")
    outfile.write(",,,,\n")
    outfile.write(",,,,\n")
    outfile.write(",,,,\n")
    outfile.write("New articles for exixting services #,"+str(new_article_for_existing_services)+",,,\n")
    outfile.write("ACOM Removed files #,"+str(acom_removed_files)+",,,\n")
    outfile.write("ACOM No Updates #,"+str(acom_no_updates)+",,,\n")
    outfile.write("Content Refresh #,"+str(conten_refresh)+",,,\n")
    outfile.write("Should Update But not update #,"+str(should_update_but_not_update_or_not)+",,,\n")
    outfile.write("Total #,"+str(total_no_exception_no_new_article_for_existing_services)+",,,\n")
    outfile.close()
    