#!/usr/bin/env python


import os
import sys
import time
import requests
import xml.etree.ElementTree as etree
from lxml import etree


import simplekml

from StringIO import StringIO

import zipfile

import os
import sys
import glob


FINAL = True

OUTPUT_DIR = 'public_html'

BASE_URL = 'https://www.procrastinatio.org/riki/'
PATH = ''

if FINAL:
    OUTPUT_DIR = 'swisstopo/cms2007/products/download/topo/FK/'
    BASE_URL = 'https://dav0.bgdi.admin.ch/'
    PATH = OUTPUT_DIR

NETWORK_LINK = 'KML_LT_FK_OA.kml'



INDEXES = ['KML_LT_FK_S20_FOR.kml', 'KML_LT_FK_GOT_FORM.kml', 'KML_LT_FK_OA.kml', 'KML_Grundlagen_Serie_1_ca__1890-1910.kml', 'KML_Grundlagen_Serie_2_ca__1910-1930.kml', 'KML_Airolo_1889-1892.kml', 'KML_Andermatt_1890-1892.kml', 'KML_Spezialkarte_Serie_1_ca__1890-1910.kml', 'KML_Spezialkarte_Serie_2_ca__1910-1930.kml', 'KML_Spezialkarte_Festungsgebiete_ca__1930-1950.kml', 'KML_Carte_ca__1910-1940.kml', 'KML_Base_ca__1910-1940.kml', 'KML_LT_FK_TIC_1946_1949.kml', 'KML_Bases_serie_1_ca__1890-1904.kml', 'KML_Carte_speciale_serie_1_ca__1890-1904.kml', 'KML_Bases_serie_2_1894-1932.kml', 'KML_Carte_speciale_serie_2_1904-1936.kml', 'KML_Carte_speciale_des_regions_fortifiees_ca__1930-1950.kml', 'KML_LT_FK_SAR_1940_1950.kml', 'KML_LT_FK_Grenzwerke.kml', 'KML_LT_FK_HEL.kml', 'KML_LT_FK_NAT.kml', 'KML_LT_FK_REU.kml', 'KML_LT_FK_RHE.kml', 'KML_LT_FK_RUE.kml', 'KML_LT_FK_VAL.kml', 'KML_LT_FK_0_B.kml', 'KML_LT_FK_0_U.kml', 'KML_LT_FK_ZEN.kml']

SOURCE_URL = 'https://dav0.bgdi.admin.ch/swisstopo/cms2007/products/download/topo/FK/'


KMZ = False


def get_index_kml(url):
    r = requests.get(url, verify=False)

    return r.text


def getLinks(content):
    links = []
    root = etree.fromstring(content)
    layers = root.findall('.//{http://www.opengis.net/kml/2.2}NetworkLink')
    for layer in layers:
        resourceurls = layer.findall('.//{http://www.opengis.net/kml/2.2}href')

        for i in resourceurls:
            links.append(i.text)

    return links


def fix_kml(content):

    parser = etree.XMLParser(strip_cdata=False)
    root = etree.fromstring(content, parser)


    doc = root.find('{http://www.opengis.net/kml/2.2}Document')

    name = doc.find('.//{http://www.opengis.net/kml/2.2}name').text

    style = root.find('.//{http://www.opengis.net/kml/2.2}Style[@id="style"]')

    # print doc, style

    # nicer style

    style1 = '''<Style id="style">
        <IconStyle>
          <scale>0</scale>
        </IconStyle>
        <LabelStyle>
           <color>ff663333</color>
        </LabelStyle>
        <LineStyle>
           <color>ff663333</color>
          <width>3</width>
        </LineStyle>
        <PolyStyle>
          <color>66cc9999</color>
        </PolyStyle>
      </Style>'''

    valid_style  = etree.fromstring(style1)

    try:
        doc.remove(style)

        doc.insert(1, valid_style)
    except TypeError as e:
        print "No style"

    # print etree.tounicode(doc)

    points = []

    name = root.find('.//{http://www.opengis.net/kml/2.2}Document/{http://www.opengis.net/kml/2.2}name').text
    # print name
    multis = root.findall('.//{http://www.opengis.net/kml/2.2}MultiGeometry')
    for multi in multis:
        for geom in multi.getchildren():
            if geom.tag == '{http://www.opengis.net/kml/2.2}Point':
                coord = geom[0].text
                # print coord
                multi.remove(geom)

                xy = [float(i.strip())  for i in coord.split(',')]

                point = {'label': name, 'coordinates': xy}

                points.append(point)

    tree = etree.ElementTree(root)

    return (etree.tounicode(tree), points)

    #tree.write("page.xml", xml_declaration=True,encoding='utf-8',method="xml",default_namespace='http://www.opengis.net/kml/2.2')


def label_kml(label_fname, points):
    kml = simplekml.Kml()

    sharedstyle = simplekml.Style()
    sharedstyle.labelstyle.color = 'ff0000ff'  # Red
    sharedstyle.labelstyle.scale = 0.7

    sharedstyle.labelstyle.color = 'ff663333'

    sharedstyle.iconstyle.scale = 0  # Icon thrice as big

    for point in points:
        # print point
        pnt = kml.newpoint(name= point['label'])
        pnt.coords = [point['coordinates']]
        pnt.style = sharedstyle

    kml.save(label_fname)


def network_link(network_fname, links):
    kml = simplekml.Kml()

    fname = os.path.basename(network_fname)
    doc_name = fname.replace('.kml', '')

    doc = kml.newdocument(name=doc_name)
    for link in links:
        link = os.path.basename(link)
        label = link.replace('.kml', '')
        netlink = kml.newnetworklink(name=label)
        netlink.link.href = BASE_URL + PATH + link
        #netlink.link.viewrefreshmode = simplekml.ViewRefreshMode.onrequest

    print "Network link written to '{}'".format(network_fname)

    kml.save(network_fname)


def zip_content(content):
    kmz = StringIO()
    f = zipfile.ZipFile(kmz, 'w', zipfile.ZIP_DEFLATED)
    f.writestr('doc.kml', content)
    f.close()
    zipped = kmz.getvalue()
    kmz.close()

    return zipped


def handle_kmls(index_name, kmls):
    removed_points = []

    print "Getting missing input KML"
    for kml in kmls:
        fname = os.path.basename(kml)
        input_name = os.path.join('input', fname)

        kml_url = BASE_URL + PATH + kml

        if not os.path.exists(input_name):
            print input_name
            r = requests.get(kml_url)
            with open(input_name,  'w') as f:
                f.write(r.text)
    print "OK all KMLs written to 'input'"
    '''kmls = glob.glob('input/*.kml')'''

    label_fname = os.path.join(OUTPUT_DIR, index_name + "_label.kml")

    print "Label file for '{}' is '{}'".format(index_name, label_fname)


    links = [label_fname]

    for kml in kmls:
        fname = os.path.basename(kml)

        if KMZ:
            fname = fname.replace('.kml', '.kmz')

        output_name = os.path.join(OUTPUT_DIR, fname)
        input_name = os.path.join('input', fname)

        with open(input_name, 'r') as f:
            c = f.read()
            links.append(output_name)

        kml, points = fix_kml(c)

        print "Fixed KML '{}' written to '{}' with {} points".format(fname, output_name, len(points))

        if KMZ:
            file_content = zip_content(kml)
        else:
            file_content = kml

        with open(output_name, 'w') as f:
            f.write(file_content)

        removed_points.extend(points)

    label_kml(label_fname, removed_points)

    print "Total number of points: {}".format(len(removed_points))

    network_fname = os.path.join(OUTPUT_DIR, index_name)

    network_link(network_fname, links)


if __name__ == "__main__":

    for index in INDEXES:  #[0:2]:
        print "\n\n===================="
        print index
        print "===================="

        url = SOURCE_URL + index

        input_name = os.path.join('input', index)
        if not os.path.exists(input_name):
            r = requests.get(url)
            if r.status_code == 200:
                print index
                with open(input_name,  'w') as f:
                    f.write(r.text)

        with open(input_name, 'r') as f:
            content = f.read()

        links = getLinks(content)

        kmls = [os.path.basename(k) for k in links if not k.endswith('label.kml')]

        print "Found {} kmls".format(len(kmls))
        print kmls

        if len(kmls) > 0:

            handle_kmls(index, kmls)


    '''xmllint  --schema /home/marco/env/lib/python2.7/site-packages/pykml/schemas/kml22gx.xsd     public_html/KML_997686934101791.kml'''
