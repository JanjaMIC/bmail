import hashlib
import hmac
import uuid
from google.appengine.ext import ndb

class Uporabnik(ndb.Model):
    ime = ndb.StringProperty()
    priimek = ndb.StringProperty()
    email = ndb.StringProperty()
    sifrirano_geslo = ndb.StringProperty()
    slika = ndb.StringProperty()

    @classmethod
    def ustvari(cls, ime, priimek, slika, email, original_geslo):
        uporabnik = cls(ime=ime, priimek=priimek, slika=slika, email=email, sifrirano_geslo=original_geslo)
        uporabnik.put()
        return uporabnik

    @classmethod
    def sifriraj_geslo(cls, original_geslo):
        salt = uuid.uuid4().hex
        sifra = hmac.new(str(salt), str(original_geslo), hashlib.sha512).hexdigest()
        return "%s:%s" % (sifra, salt)

    @classmethod
    def preveri_geslo(cls, original_geslo, uporabnik):
        sifra, salt = uporabnik.sifrirano_geslo.split(":")
        preverba = hmac.new(str(salt), str(original_geslo), hashlib.sha512).hexdigest()

        if preverba == sifra:
            return True
        else:
            return False




class Sporocilo(ndb.Model):
    naslov = ndb.StringProperty()
    vsebina = ndb.StringProperty()
    idposiljatelja = ndb.StringProperty()  # to nbe bo string"
    idprejemnika = ndb.StringProperty()  # to ne bo string
    ustvarjeno = ndb.DateTimeProperty(auto_now_add=True)