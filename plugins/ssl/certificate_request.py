#!/usr/bin/env python

# Rapache - Apache Configuration Tool
# Copyright (C) 2008 Stefano Forenza,  Jason Taylor, Emanuele Gentili
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""".
Issues with the new window:
    - self.parent doesn't work
    - onblur doesn't trigger when pressing Return
    - changing a domain name doesn't change subdomains
    - empty server aliases shuoldn't be managed
ALSO:
    - please implement a delete directive func in the parser
    - move denorm. vhosts in another tab
    - merge with Qense warning window
"""

import sys
import re
import locale
import time
from OpenSSL import crypto
try:
     import pygtk
     pygtk.require("2.0")
except:
      pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import os
import pango
import tempfile
import traceback
import RapacheGtk.GuiUtils
from RapacheCore.Module import *
from RapacheGtk import GuiUtils
import RapacheGtk.DesktopEnvironment as Desktop
import RapacheCore.Shell
from text_display import TextDisplayWindow
country_codes = {"ALAND ISLANDS":"AX",
"ALBANIA":"AL",
"ALGERIA":"DZ",
"AMERICAN SAMOA":"AS",
"ANDORRA":"AD",
"ANGOLA":"AO",
"ANGUILLA":"AI",
"ANTARCTICA":"AQ",
"ANTIGUA AND BARBUDA":"AG",
"ARGENTINA":"AR",
"ARMENIA":"AM",
"ARUBA":"AW",
"AUSTRALIA":"AU",
"AUSTRIA":"AT",
"AZERBAIJAN":"AZ",
"BAHAMAS":"BS",
"BAHRAIN":"BH",
"BANGLADESH":"BD",
"BARBADOS":"BB",
"BELARUS":"BY",
"BELGIUM":"BE",
"BELIZE":"BZ",
"BENIN":"BJ",
"BERMUDA":"BM",
"BHUTAN":"BT",
"BOLIVIA":"BO",
"BOSNIA AND HERZEGOVINA":"BA",
"BOTSWANA":"BW",
"BOUVET ISLAND":"BV",
"BRAZIL":"BR",
"BRITISH INDIAN OCEAN TERRITORY":"IO",
"BRUNEI DARUSSALAM":"BN",
"BULGARIA":"BG",
"BURKINA FASO":"BF",
"BURUNDI":"BI",
"CAMBODIA":"KH",
"CAMEROON":"CM",
"CANADA":"CA",
"CAPE VERDE":"CV",
"CAYMAN ISLANDS":"KY",
"CENTRAL AFRICAN REPUBLIC":"CF",
"CHAD":"TD",
"CHILE":"CL",
"CHINA":"CN",
"CHRISTMAS ISLAND":"CX",
"COCOS (KEELING) ISLANDS":"CC",
"COLOMBIA":"CO",
"COMOROS":"KM",
"CONGO":"CG",
"CONGO, THE DEMOCRATIC REPUBLIC OF THE":"CD",
"COOK ISLANDS":"CK",
"COSTA RICA":"CR",
"COTE D'IVOIRE":"CI",
"CROATIA":"HR",
"CUBA":"CU",
"CYPRUS":"CY",
"CZECH REPUBLIC":"CZ",
"DENMARK":"DK",
"DJIBOUTI":"DJ",
"DOMINICA":"DM",
"DOMINICAN REPUBLIC":"DO",
"ECUADOR":"EC",
"EGYPT":"EG",
"EL SALVADOR":"SV",
"EQUATORIAL GUINEA":"GQ",
"ERITREA":"ER",
"ESTONIA":"EE",
"ETHIOPIA":"ET",
"FALKLAND ISLANDS (MALVINAS)":"FK",
"FAROE ISLANDS":"FO",
"FIJI":"FJ",
"FINLAND":"FI",
"FRANCE":"FR",
"FRENCH GUIANA":"GF",
"FRENCH POLYNESIA":"PF",
"FRENCH SOUTHERN TERRITORIES":"TF",
"GABON":"GA",
"GAMBIA":"GM",
"GEORGIA":"GE",
"GERMANY":"DE",
"GHANA":"GH",
"GIBRALTAR":"GI",
"GREECE":"GR",
"GREENLAND":"GL",
"GRENADA":"GD",
"GUADELOUPE":"GP",
"GUAM":"GU",
"GUATEMALA":"GT",
"GUERNSEY":"GG",
"GUINEA":"GN",
"GUINEA-BISSAU":"GW",
"GUYANA":"GY",
"HAITI":"HT",
"HEARD ISLAND AND MCDONALD ISLANDS":"HM",
"HOLY SEE (VATICAN CITY STATE)":"VA",
"HONDURAS":"HN",
"HONG KONG":"HK",
"HUNGARY":"HU",
"ICELAND":"IS",
"INDIA":"IN",
"INDONESIA":"ID",
"IRAN, ISLAMIC REPUBLIC OF":"IR",
"IRAQ":"IQ",
"IRELAND":"IE",
"ISLE OF MAN":"IM",
"ISRAEL":"IL",
"ITALY":"IT",
"JAMAICA":"JM",
"JAPAN":"JP",
"JERSEY":"JE",
"JORDAN":"JO",
"KAZAKHSTAN":"KZ",
"KENYA":"KE",
"KIRIBATI":"KI",
"KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF":"KP",
"KOREA, REPUBLIC OF":"KR",
"KUWAIT":"KW",
"KYRGYZSTAN":"KG",
"LAO PEOPLE'S DEMOCRATIC REPUBLIC":"LA",
"LATVIA":"LV",
"LEBANON":"LB",
"LESOTHO":"LS",
"LIBERIA":"LR",
"LIBYAN ARAB JAMAHIRIYA":"LY",
"LIECHTENSTEIN":"LI",
"LITHUANIA":"LT",
"LUXEMBOURG":"LU",
"MACAO":"MO",
"MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF":"MK",
"MADAGASCAR":"MG",
"MALAWI":"MW",
"MALAYSIA":"MY",
"MALDIVES":"MV",
"MALI":"ML",
"MALTA":"MT",
"MARSHALL ISLANDS":"MH",
"MARTINIQUE":"MQ",
"MAURITANIA":"MR",
"MAURITIUS":"MU",
"MAYOTTE":"YT",
"MEXICO":"MX",
"MICRONESIA, FEDERATED STATES OF":"FM",
"MOLDOVA":"MD",
"MONACO":"MC",
"MONGOLIA":"MN",
"MONTENEGRO":"ME",
"MONTSERRAT":"MS",
"MOROCCO":"MA",
"MOZAMBIQUE":"MZ",
"MYANMAR":"MM",
"NAMIBIA":"NA",
"NAURU":"NR",
"NEPAL":"NP",
"NETHERLANDS":"NL",
"NETHERLANDS ANTILLES":"AN",
"NEW CALEDONIA":"NC",
"NEW ZEALAND":"NZ",
"NICARAGUA":"NI",
"NIGER":"NE",
"NIGERIA":"NG",
"NIUE":"NU",
"NORFOLK ISLAND":"NF",
"NORTHERN MARIANA ISLANDS":"MP",
"NORWAY":"NO",
"OMAN":"OM",
"PAKISTAN":"PK",
"PALAU":"PW",
"PALESTINIAN TERRITORY, OCCUPIED":"PS",
"PANAMA":"PA",
"PAPUA NEW GUINEA":"PG",
"PARAGUAY":"PY",
"PERU":"PE",
"PHILIPPINES":"PH",
"PITCAIRN":"PN",
"POLAND":"PL",
"PORTUGAL":"PT",
"PUERTO RICO":"PR",
"QATAR":"QA",
"REUNION":"RE",
"ROMANIA":"RO",
"RUSSIAN FEDERATION":"RU",
"RWANDA":"RW",
"SAINT BARTHELEMY":"BL",
"SAINT HELENA":"SH",
"SAINT KITTS AND NEVIS":"KN",
"SAINT LUCIA":"LC",
"SAINT MARTIN":"MF",
"SAINT PIERRE AND MIQUELON":"PM",
"SAINT VINCENT AND THE GRENADINES":"VC",
"SAMOA":"WS",
"SAN MARINO":"SM",
"SAO TOME AND PRINCIPE":"ST",
"SAUDI ARABIA":"SA",
"SENEGAL":"SN",
"SERBIA":"RS",
"SEYCHELLES":"SC",
"SIERRA LEONE":"SL",
"SINGAPORE":"SG",
"SLOVAKIA":"SK",
"SLOVENIA":"SI",
"SOLOMON ISLANDS":"SB",
"SOMALIA":"SO",
"SOUTH AFRICA":"ZA",
"SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS":"GS",
"SPAIN":"ES",
"SRI LANKA":"LK",
"SUDAN":"SD",
"SURINAME":"SR",
"SVALBARD AND JAN MAYEN":"SJ",
"SWAZILAND":"SZ",
"SWEDEN":"SE",
"SWITZERLAND":"CH",
"SYRIAN ARAB REPUBLIC":"SY",
"TAIWAN, PROVINCE OF CHINA":"TW",
"TAJIKISTAN":"TJ",
"TANZANIA, UNITED REPUBLIC OF":"TZ",
"THAILAND":"TH",
"TIMOR-LESTE":"TL",
"TOGO":"TG",
"TOKELAU":"TK",
"TONGA":"TO",
"TRINIDAD AND TOBAGO":"TT",
"TUNISIA":"TN",
"TURKEY":"TR",
"TURKMENISTAN":"TM",
"TURKS AND CAICOS ISLANDS":"TC",
"TUVALU":"TV",
"UGANDA":"UG",
"UKRAINE":"UA",
"UNITED ARAB EMIRATES":"AE",
"UNITED KINGDOM":"GB",
"UNITED STATES":"US",
"UNITED STATES MINOR OUTLYING ISLANDS":"UM",
"URUGUAY":"UY",
"UZBEKISTAN":"UZ",
"VANUATU":"VU",
"VATICAN CITY STATE":"see HOLY SEE",
"VENEZUELA":"VE",
"VIET NAM":"VN",
"VIRGIN ISLANDS, BRITISH":"VG",
"VIRGIN ISLANDS, U.S.":"VI",
"WALLIS AND FUTUNA":"WF",
"WESTERN SAHARA":"EH",
"YEMEN":"YE",
"ZAMBIA":"ZM",
"ZIMBABWE":"ZW"}

class CertificateRequestWindow:
    
    def __init__(self, path):
    
    
        # The path to the plugin
        self.glade_path = path
                  
        gladefile = os.path.join(path,"vhost.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_ssl_certificate_request")
        
        #self.text_view_module_conf = wtree.get_widget("text_view_module_conf")
        self.combobox_domain = wtree.get_widget("combobox_domain")
        self.combobox_country = wtree.get_widget("combobox_country")
        self.entry_state = wtree.get_widget("entry_state")
        self.entry_city = wtree.get_widget("entry_city")
        self.entry_organisation = wtree.get_widget("entry_organisation")
        self.entry_organisation_unit = wtree.get_widget("entry_organisation_unit")
        self.button_ok = wtree.get_widget("button_ok")
        self.button_cancel = wtree.get_widget("button_cancel")
        self.label_warning = wtree.get_widget("label_warning")
        self.checkbutton_self_sign = wtree.get_widget("checkbutton_self_sign")

        signals = {
           "on_button_ok_clicked"           : self.on_button_ok_clicked,
           "on_button_cancel_clicked"         : self.on_button_cancel_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)

       
        
    def on_button_ok_clicked(self, widget):
        self.generate_certificate_request()
        self.window.destroy()
        return
        
    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return

    def run(self):
        self.window.show_all()   
        self.label_warning.set_size_request(self.label_warning.get_parent().size_request()[0], -1)
        gtk.main()
        
        return self.cert
   
    
    def generate_certificate_request(self):
        # http://www.iaeste.or.at/doc/pyopenssl-doc/examples/
        
        # Generate a key for the vhost
        self.cert = None
        path = os.path.join(self.path)
        timestamp = time.strftime("%y-%m-%d %H:%M:%S", time.localtime() )
        privatekey_path = os.path.join(path, self.combobox_domain.get_active_text() + '.pkey')
        certreq_path = os.path.join(path, self.combobox_domain.get_active_text() +  ' ' + timestamp +'.csr')
        cert_path = os.path.join(path, self.combobox_domain.get_active_text() +  ' ' + timestamp +'.cert')
       
        pkey = crypto.PKey()
        if not Shell.command.exists(privatekey_path):
            Shell.command.create_complete_path(path)
            pkey.generate_key(crypto.TYPE_RSA, 1024)
            Shell.command.write_file( privatekey_path, crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        else:
            pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, Shell.command.read_file(privatekey_path)) 
            
        req = crypto.X509Req()
        subj = req.get_subject()
        setattr(subj, "CN", self.combobox_domain.get_active_text())
        setattr(subj, "C", country_codes[self.combobox_country.get_active_text()])
        if self.entry_city.get_text():
            setattr(subj, "L", self.entry_city.get_text()) 
        if self.entry_organisation.get_text():
            setattr(subj, "O", self.entry_organisation.get_text())    
        if self.entry_organisation_unit.get_text():
            setattr(subj, "OU", self.entry_organisation_unit.get_text()) 
        if self.entry_state.get_text():
            setattr(subj, "ST", self.entry_state.get_text())    

        req.set_pubkey(pkey)
        req.sign(pkey, "md5")

        Shell.command.write_file( certreq_path, crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))


        if self.checkbutton_self_sign.get_active():
            cert = crypto.X509()
            cert.set_serial_number(0)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(60*60*24*365*5) # five years
            cert.set_issuer(req.get_subject())
            cert.set_subject(req.get_subject())
            cert.set_pubkey(req.get_pubkey())
            cert.sign(pkey, "md5")
            Shell.command.write_file( cert_path, crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            self.cert = cert_path
        else:
        
            tdw = TextDisplayWindow(self.glade_path)
            tdw.load( "You will need to send this certificate request, proof of your company's identity, and payment to a Certificate Authority (CA). The CA verifies the certificate request and your identity, and then sends back a certificate for your secure server.", certreq_path)
            tdw.run()
        return
    

    def load (self, domains, email, path):
        self.path = path
        
        # Attempt to detect country code
        code, enc = locale.getdefaultlocale()
        code = code[-2:].upper()
        keys = country_codes.keys()
        keys.sort()
        count = 0
        for key in keys:
            self.combobox_country.append_text(key)
            if country_codes[key] == code:
                self.combobox_country.set_active(count)
            count = count + 1
    
        for domain in domains:
            self.combobox_domain.append_text(domain)
            self.combobox_domain.append_text("*."+ domain) # add sub domain wildcard
            
        self.combobox_domain.set_active(0)
        
        return
				
    def on_destroy(self, widget, data=None):
        gtk.main_quit()

