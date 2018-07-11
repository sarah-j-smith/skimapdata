## Requires Python 3 
##  Install it via brew if you don't have it & use a virtual env 
##     https://gist.github.com/sarah-j-smith/1a054d5efa3ee7f32c1ee52f17a8a0f1

import xml.etree.ElementTree as ET
import urllib
import urllib.request
import time
import io
import zipfile
import requests

# Use a tolerant XML parser for KML files
from lxml.html import soupparser
from lxml.etree import XMLParser
from lxml.etree import XMLSyntaxError
from lxml import etree as LT
kml_parser = XMLParser(ns_clean=True, recover=True, remove_comments=True)

# The skimap.org XML files are well formed
tree = ET.parse("ski_areas.xml")
root = tree.getroot()
ski_area_count = len(root)

def read_xml(xml_file, xml_url):
    try:
        kml_xml = ET.parse(xml_file, parser=kml_parser)
        kml_root = kml_xml.getroot()
        node_count = len(kml_root)
        if node_count > 0:
            return kml_root
    except ET.ParseError:
        #print(f"ET Could not parse {xml_url}")
        pass
    except XMLSyntaxError:
        #print(f"BS Could not parse {xml_url}")
        pass
    except Exception as e:
        #print(e)
        #print(f"File error {xml_url}")
        pass
    return None

def process_url(kml_url):
    kml_req = requests.get(kml_url, allow_redirects=False)
    try:
        kml_req.raise_for_status()
        xml_memory_file = io.BytesIO(kml_req.content)
        result = None
        if kml_url.endswith("kmz"):
            if zipfile.is_zipfile(xml_memory_file):
                zipcontent = zipfile.ZipFile(xml_memory_file)
                names = zipcontent.namelist()
                with zipcontent.open(names[0]) as zipfile_unzipped:
                    result = read_xml(zipfile_unzipped, kml_url)
        else:
            result = read_xml(xml_memory_file, kml_url)
        return result
    except requests.exceptions.HTTPError as e:
        fail_code = kml_req.status_code
        if fail_code != 302:
            print(f"fetch KML {kml_url} failed with {fail_code}")
    return None

print(f"Scanning {ski_area_count} ski areas")
for run in root:

    runId = run.attrib["id"]
    runName = run.find("name").text
    print(f"* {runName}")

    # Fetch the details for this field
    details_url = f"https://skimap.org/SkiAreas/view/{runId}.xml"
    map_view_root = process_url(details_url)

    if map_view_root.find("openSkiMaps") == None:
        print("   No Open Ski Map data listed")
        continue

    # There is some OSM data in the details, get the XML
    # 	<openSkiMaps>
    #       <openSkiMap id="2490" date="2011-03-25" />
    #       <openSkiMap id="2218" date="2011-03-22" />
    # 	</openSkiMaps>
    # ET.dump(map_view_details)

    map_id = map_view_root.attrib["id"]
    osm_info = map_view_root.findall("openSkiMaps/*")
    osm_count = len(osm_info)
    print(f"    trying {osm_count} OSM records")

    # note that most recent files are listed in the XML first
    # so break as soon as we find something useable
    kml_found = None
    kml_fn = None
    for osm in osm_info:
        osm_id = osm.attrib["id"]
        osm_date = osm.attrib["date"]
        # print(f"    id: {osm_id} - date: {osm_date}")

        kml_url = f"https://skimap.org/data/{map_id}/osm/kml/{osm_date}.kml"
        # print("    trying KML url")
        kml_out = process_url(kml_url)
        if kml_out == None:
            kmz_url = f"https://skimap.org/data/{map_id}/osm/kmz/{osm_date}.kmz"
            kml_out = process_url(kmz_url)

        if kml_out != None:
            tree_out = ET.ElementTree(kml_out)
            kml_fn = f"osm-ski-area-{map_id}.kml"
            # tree_out.write("unfilt-" + kml_fn, encoding="utf-8")
            kml_found = kml_out
        else:
            print(f"    No KML for {osm_id}  :-(")

        time.sleep(0.5)

        # if we found some KML, exit & just use that; don't fetch
        # previous ones - assumes latest is best.
        if kml_found != None:
            break

    if kml_found != None:
        filtered_xml = LT.Element('kml')
        doc_el = LT.SubElement(filtered_xml, 'Document')
        poi_folder = LT.SubElement(doc_el, 'Folder')
        name_tag = LT.SubElement(poi_folder, 'name')
        description_tag = LT.SubElement(poi_folder, 'description')
        description_tag.text = "Points of Interest"
        name_tag.text = "POI"
        #    <Folder>
        #       <name>POI</name>
        #         <description>Points of Interest</description>
        
        color_tags = kml_found.findall(".//color")
        for col in color_tags:
            col_val = col.text
            if col_val.startswith("#"):
                col_val = col_val[1:]
                col.text = col_val

        snippets = kml_found.findall(".//Snippet")
        for snip in snippets:
            snip_parent = snip.getparent()
            snip_parent.remove(snip)
        hotel_frags = kml_found.findall(".//Folder[name='Hotel']")
        restaurant_frags = kml_found.findall(".//Folder[name='Restaurant']")
        lifts_frags = kml_found.findall(".//Folder[name='Ski_Lift']")
        routes_frags = kml_found.findall(".//Folder[name='Ski_Routes']")
        ski_run_frags = kml_found.findall(".//Folder[name='Ski_Runs']")
        
        poi_folder.extend(hotel_frags)
        poi_folder.extend(restaurant_frags)
        doc_el.extend(lifts_frags)
        doc_el.extend(routes_frags)
        doc_el.extend(ski_run_frags)

        tree_printed = LT.tostring(filtered_xml, pretty_print=True)
        tree_file = open(kml_fn, "wb")
        tree_file.write(tree_printed)
        tree_file.close()
        print(f"   > {kml_fn}")
