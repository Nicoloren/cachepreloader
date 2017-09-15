# -*- coding: utf-8 -*-
# library to manage GUI 
# Author : Nicolas Lorenzon - www.lorenzon.ovh - nicolas@lorenzon.ovh
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import threading, socket

import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
import time, threading, random
import pprint
from bs4 import BeautifulSoup, SoupStrainer
import os.path
import lxml.html
import webbrowser
import queue
# librairie pour les accès à la base de données
import lib_bd

class MyQueue(queue.Queue): # or OrderedSetQueue
    def __contains__(self, item):
        with self.mutex:
            return item in self.queue

class myGui(object):

    def __init__(self):
        
        self.fenetre = None

        # tree des sites fentre générale
        self.tree = None

        self.idModification = None
        self.idModificationAction = None

        self.entryUrl = None
        self.entryExclusion = None
        self.label_compteur = None

        self.termes_a_exclure = None

        # les queues pour gérer correctement le multithreading

        self.queueUrlsEnAttente = None
        self.queueUrlsTraitees = None
        self.queueUrls = None

        self.thread = None

        self.stopThread = False

        self.initialisation()
        self.addWidgets()
        self.runLoop()
        
    def initialisation(self) :
        # init GUI
        self.fenetre = Tk()
        #self.fenetre.iconbitmap(ICON_PATH)
        self.fenetre.title("Cache Preloader version 20160802")
        self.fenetre.geometry("1200x600")
        

    # Fonction qui va lire un fichier et retourner toutes les lignes
    def lireFichier(self, fichier) :
        with open(fichier,encoding='utf-8') as f:
            content = f.readlines()
        return content
        
    # lecture du fichier de configuration s'il existe
    # renvoie un couple d'éléments : site et config
    def readConfig(self) :
         website = "http://www.seosoftwarenow.com"
         # wordpress : /tag/, /author/, /comment-subscriptions, /wp-login, /wp-admin, /feed/, /wp-content/, /trackback/, /archives/
         configuration = ".img, .png, .gif, .jpeg, .jpg, .zip, .rar, .mp4, .mov, .mpeg, .css, .js"
         
         if (os.path.isfile("config.cfg")) :
             #print("fichier config trouvé")
             contenu = self.lireFichier("config.cfg")
             #print(contenu)
             for ligne in contenu :
                 # on regarde si on trouve les mots clés
                 if ("SITE=" in ligne) :
                     website = ligne.replace("SITE=", "").replace("\n", "").replace(" ", "")
                 if ("CONFIG=" in ligne) :
                     configuration = ligne.replace("CONFIG=", "").replace("\n", "").replace(" ", "")
         else :
             print("fichier config non trouvé")
             
         return configuration, website



    # ajout des widget sur la fenetre principale des sites
    def addWidgets(self) :
        
        # reste interface.......................................................
        frame1 = Frame(self.fenetre, borderwidth=2, relief=GROOVE)
        frame1.pack(side=TOP, padx=5, pady=5, expand=False, fill=X)

        bouton=Button(frame1, text="Quit", command=self.quitter)
        bouton.pack(side="right", padx=5, pady=5)

        button = Button(frame1, text="Preload Cache", command=self.crawl)
        button.pack(side="left", padx=5, pady=5)

        button = Button(frame1, text="Stop cache preloading", command=self.stopcrawl)
        button.pack(side="left", padx=5, pady=5)

        # lecture de la configuration
        configurationConfig, websiteConfig = self.readConfig()
        print(websiteConfig)
        print(configurationConfig)

        self.entryUrl = Entry(frame1, width=30)
        self.entryUrl.pack(side="left", fill=X, expand=True)
        self.entryUrl.insert(0, websiteConfig)

        # pour la liste d'exclusion
        frame3 = Frame(self.fenetre, borderwidth=2, relief=GROOVE)
        frame3.pack(side=TOP, padx=5, pady=5, expand=False, fill=X)

        w = Label(frame3, text="Do not crawl url with (comma separated) : ")
        w.pack(side="left", padx=5, pady=5)

        self.entryExclusion = Entry(frame3, width=30)
        self.entryExclusion.pack(side="left", fill=X, expand=True)
        self.entryExclusion.insert(0, configurationConfig)
 
        # affichage de la liste des pages parcourues
        frame2 = Frame(self.fenetre, borderwidth=2, relief=GROOVE)
        frame2.pack(side=TOP, padx=5, pady=5, expand=True, fill=BOTH)

        scrollbar = Scrollbar(frame2)
        scrollbar.pack(side = RIGHT, fill=Y )

        self.tree = Treeview(frame2)
        self.tree.heading('#0', text='Urls')
        #self.tree["columns"]=("url")
        self.tree.column("#0",minwidth=200,width=1000, stretch=YES)
        self.tree.pack(side="right", padx=5, pady=5, expand=True, fill=BOTH)

        scrollbar.config(command=self.tree.yview)
        self.tree.config(yscrollcommand=scrollbar.set)
        
        # frame avec compteur
        frame4 = Frame(self.fenetre, borderwidth=2, relief=GROOVE)
        frame4.pack(side=TOP, padx=5, pady=5, expand=False, fill=X)

        self.label_compteur = StringVar()
        w = Label(frame4, textvariable=self.label_compteur)
        w.pack(side="right", padx=5, pady=5)
        self.label_compteur.set("0 url crawled")
        
        w = Label(frame4, text="Use at your own risk - Get help on SeoSoftwareNow.com")
        w.pack(side="left", padx=5, pady=5)

    def quitter(self) :
        self.stopcrawl()
        self.fenetre.quit()
        print("elements traités :")
        while True :
            if self.queueUrlsTraitees.empty() :
                break
            else :
                elem = self.queueUrlsTraitees.get()
                print(elem)

        print("elements connus :")
        while True :
            if self.queueUrls.empty() :
                break
            else :
                elem = self.queueUrls.get()
                print(elem)

    def processOneUrl(self, url, threadNumber):

        if url not in self.queueUrlsTraitees :
            self.queueUrlsTraitees.put(url)
            self.tree.insert("", 0, text=str(url))

        if url not in self.queueUrls :
            self.queueUrls.put(url)
            
        try:
            traitement = False
            try :
                print (str(threadNumber) + " (process on url - download) : " + str(url))
                html_page = urllib.request.urlopen(url, timeout=5).read()
                traitement = True
            except urllib.error.URLError as e:
                #print(e.reason) 
                print(" **** Erreur request **** : " + str(e.reason))
            except socket.timeout:
                print(" **** Erreur request **** : socket.timeout")
            except Exception :
                print(" **** Exception non connue ****")
            if traitement : 
                print (str(threadNumber) + " (process on url - lxml) : " + str(url))
                # test avec lxml
                html = lxml.html.fromstring(html_page)
                #print (str(threadNumber) + " (process on url - lxml - make_links_absolute) : " + str(url))
                html.make_links_absolute(url, resolve_base_href=True)
                #print (str(threadNumber) + " (process on url - lxml - xpath) : " + str(url))
                urls = html.xpath('//a/@href', smart_strings=False)
                #print(urls)
                #print (str(threadNumber) + " (process on url - lxml - boucle) : " + str(url))
                url_de_base = self.entryUrl.get()
                for linkO in urls:
                    linkOs = linkO.split("#")
                    if len(linkOs) > 1 :
                        link = linkOs[0]
                    else :
                        link = linkO
                    if link.startswith(url_de_base):
                        if link not in self.queueUrlsTraitees:
                            if link not in self.queueUrlsEnAttente :
                                if link is not "":
                                    self.queueUrlsEnAttente.put(link)
                                    self.queueUrls.put(link)
            
        except ValueError:
            print(" *** il y a eu un problème : " + str(ValueError))

    # on trouve la prochaine url à crawler
    def moreToCrawl(self, threadNumber):

        if not self.queueUrlsEnAttente.empty():
            url = self.queueUrlsEnAttente.get()
        else:
            url = None
       
        if ( url is not None ) :
            try:
                print(str(threadNumber) + " : (more to crawl) " + url)
            except:
                print("erreur encodage url")
            return url
        else :
            print("URL VIDE !!! - moretoCrawl")
        return False

    # crawl du site (lancé depuis le bouton de l'interface)
    def crawl(self) :
        #print("crawl du site")
        # mise en route avec une première url
        self.stopThread = False
        self.fenetre.config(cursor="watch")

        # on récupère les termes à exclure sous la forme d'une liste
        self.termes_a_exclure = self.entryExclusion.get().replace(" ", "").split(",")
        # print(self.termes_a_exclure)

        # gestion avec des queues
        self.queueUrlsEnAttente = MyQueue()
        self.queueUrlsTraitees = MyQueue()
        self.queueUrls = MyQueue()

        # on utilise des queues pour gérer le démarrage
        # et on renseigne une première url comme début
        self.queueUrls.put(self.entryUrl.get())
        self.queueUrlsEnAttente.put(self.entryUrl.get())
        
        self.thread = threading.Thread(target=self.crawltout, args=())
        self.thread.start()

    # on regarde si on doit crawler cette url ou non
    # on ne la crawle pas si elle est dans les termes à exclure
    def on_crawl(self, url) :
        on_crawl = True
        if self.termes_a_exclure is None :
            return on_crawl
        if (len(self.termes_a_exclure) <= 0) :
            return on_crawl
            
        for element in self.termes_a_exclure :
            
            if (element != "") : # cas on a rien exclu
                if element in url :
                    on_crawl = False
                    # on l'indique comme crawlée
                    if url not in self.queueUrlsTraitees :
                        self.queueUrlsTraitees.put(url)
                    break
        return on_crawl

    # un seul thread, on peut lancer plusieures fois cette fonction pour faire du multithread
    def crawltoutUnSeul(self, threadNumber) :

        # boucle sur les urls
        while True:
            if self.stopThread :
                break
            toCrawl = self.moreToCrawl(threadNumber)
            print(toCrawl)
            if not toCrawl:
                break
            # on regarde déjà si on doit crawler l'url
            if self.on_crawl(toCrawl) : 
                self.processOneUrl(toCrawl, threadNumber)
            self.maj_compteur()

        # fin traitement
        self.fenetre.config(cursor="")
    
    # rajout pour le multi-thread
    def crawltout(self):
        #self.connexion = lib_bd.connexionBase(self.base)
        #self.crawltoutUnSeul("Thread 0")
        for i in range(0, 100) :
            thread = threading.Thread(target=self.crawltoutUnSeul, args=(("Thread " + str(i),)))
            thread.start()
            if self.stopThread :
                break
            else :
                time.sleep(1)

    def stopcrawl(self) :
        # self.thread.join() # bloque tout en attendant la fin
        self.stopThread = True


    def maj_compteur(self) :
        self.label_compteur.set(str(self.queueUrlsTraitees.qsize()) + " / " + str(self.queueUrls.qsize()) + " urls")

    # boucle principale TKinter
    def runLoop(self) :
        self.fenetre.mainloop()
