#!/usr/bin/env python
import os
import jinja2
import webapp2
import cgi
from google.appengine.ext import ndb
from models import Uporabnik, Mail
from datetime import datetime
from secret import secret
import json
import hmac
import time
import datetime
import hashlib
from google.appengine.api import urlfetch



template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))

    def ustvari_cookie(self, uporabnik):
        uporabnik_id = uporabnik.key.id()
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=10)
        expires_ts = int(time.mktime(expires.timetuple()))
        sifra = hmac.new(str(uporabnik_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()
        vrednost = "{0}:{1}:{2}".format(uporabnik_id, sifra, expires_ts)
        self.response.set_cookie(key="uid", value=vrednost, expires=expires)

    def preveri_cookie(self, cookie_vrednost):
        uporabnik_id, sifra, expires_ts = cookie_vrednost.split(":")

        if datetime.datetime.utcfromtimestamp(float(expires_ts)) > datetime.datetime.now():
            preverba = hmac.new(str(uporabnik_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()

            if sifra == preverba:
                return True
            else:
                return False
        else:
            return False

    def render_template(self, view_filename, params=None):
            if not params:
                params = {}

            cookie_value = self.request.cookies.get("uid")

            if cookie_value:
                params["logiran"] = self.preveri_cookie(cookie_vrednost=cookie_value)
            else:
                params["logiran"] = False

            template = jinja_env.get_template(view_filename)
            self.response.out.write(template.render(params))



class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("hello.html")


    def post(self):
        email = self.request.get("email")
        geslo = self.request.get("geslo")

        uporabnik = Uporabnik.query(Uporabnik.email == email).get()

        if Uporabnik.preveri_geslo(original_geslo=geslo, uporabnik=uporabnik):
            self.ustvari_cookie(uporabnik=uporabnik)
            self.redirect("/prikazi_vsa_sporocila")
        else:
            self.redirect("/login")


class RegistracijaHandler(BaseHandler):
   def get(self):
       return self.render_template("registracija.html")

   def post(self):
       ime = self.request.get("ime")
       email = self.request.get("email")
       geslo = self.request.get("geslo")
       ponovno_geslo = self.request.get("ponovno_geslo")

       if geslo == ponovno_geslo:
           Uporabnik.ustvari(ime=ime, email=email, original_geslo=geslo)
           return self.redirect_to("/")


class LoginHandler(BaseHandler):
    def get(self):
        return self.render_template("login.html")

    def post(self):
        email = self.request.get("email")
        geslo = self.request.get("geslo")

        uporabnik = Uporabnik.gql("WHERE email='" + email +"'").get()

        if Uporabnik.preveri_geslo(original_geslo=geslo, uporabnik=uporabnik):
            self.ustvari_cookie(uporabnik=uporabnik)
            self.redirect("/")
        else:
            self.write("NO NO :(")




class WeatherHandler(BaseHandler):
    def get(self):
        url = "http://api.openweathermap.org/data/2.5/weather?q=London,uk&units=metric&appid=2456c1752bcf16c3b326651ac10cf0ac"
        
        result = urlfetch.fetch(url)
        
        podatki = json.loads(result.content)
        
        params = {"podatki": podatki}
        
        self.render_template("vreme.html", params)


class PosljiSporociloHandler(BaseHandler):
    def get(self):
        return self.render_template("poslano.html")


    def post(self):
        zadeva = self.request.get("zadeva")
        vsebina = self.request.get("vsebina")
        email = self.request.get("email")
        zadeva = cgi.escape(zadeva)
        vsebina = cgi.escape(vsebina)
#patricija
        cookie_value = self.request.cookies.get("uid")
        idposiljatelja, _, _ = cookie_value.split(":")
        idposiljatelja = int(idposiljatelja)
        prejemnik = Uporabnik.gql("WHERE email='"+ email +"'").get()
        idprejemnika = prejemnik.key.id()
        sporocilo = Mail(idprejemnika=idprejemnika, idposiljatelja=idposiljatelja, email=email,zadeva=zadeva, vsebina=vsebina)
        sporocilo.put()

        self.redirect("/prikazi_vsa_sporocila")
#patricija
class PrikaziSporocilaHandler(BaseHandler):
    def get(self):
        vsa_sporocila = Mail.query().order(Mail.ustvarjeno).fetch()

        view_vars = {
            "vsa_sporocila": vsa_sporocila
        }

        return self.render_template("prikazi_vsa_sporocila.html", view_vars)


class PosameznoSporociloHandler(BaseHandler):
    def get(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))

        view_vars = {
            "sporocilo": sporocilo
        }

        return self.render_template("posamezno_sporocilo.html", view_vars)


class UrediSporociloHandler(BaseHandler):
    def get(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))

        view_vars = {
            "sporocilo": sporocilo
        }

        return self.render_template("uredi_sporocilo.html", view_vars)

    def post(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))
        sporocilo.zadeva = self.request.get("zadeva")
        sporocilo.vsebina = int(self.request.get("vsebina"))
        sporocilo.idprejemnika = self.request.get("idprejemnika")
        sporocilo.put()

        self.redirect("/sporocilo/" + sporocilo_id)


    def post(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))
        sporocilo.zadeva = self.request.get("zadeva")
        sporocilo.vsebina = int(self.request.get("vsebina"))
        sporocilo.idprejemnika = self.request.get("idprejemnika")
        sporocilo.put()

        self.redirect("/sporocilo/" + int(sporocilo_id))

class IzbrisiSporociloHandler(BaseHandler):
    def get(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))

        view_vars = {
            "sporocilo": sporocilo
        }

        return self.render_template("izbrisi_sporocilo.html", view_vars)

    def post(self, sporocilo_id):
        sporocilo = Mail.get_by_id(int(sporocilo_id))
        sporocilo.key.delete()

        self.redirect("/prikazi_vsa_sporocila")

app = webapp2.WSGIApplication([
   webapp2.Route('/', MainHandler),
   webapp2.Route('/login', LoginHandler),
   webapp2.Route('/registracija', RegistracijaHandler),
   webapp2.Route('/poslano', PosljiSporociloHandler),
   webapp2.Route('/vreme', WeatherHandler),
   webapp2.Route('/prikazi_vsa_sporocila', PrikaziSporocilaHandler),
   webapp2.Route('/sporocilo/<sporocilo_id:\d+>', PosameznoSporociloHandler),
   webapp2.Route('/sporocilo/<sporocilo_id:\d+>/uredi', UrediSporociloHandler),
   webapp2.Route('/sporocilo/<sporocilo_id:\d+>/izbrisi', IzbrisiSporociloHandler),
], debug=True)


