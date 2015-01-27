#!/usr/bin/env python
'''
Created on Jan 25, 2015

@author: anshuman
'''
import urllib
import urllib2
from bs4 import BeautifulSoup
import json
import re

url = 'http://www.northamptonshireanalysis.co.uk/data/csv?viewId=151&geoId=28&subsetId=&viewer=CSV'

class DataFetcher():
    ''' 
    Helper class to navigate & fetch the static datasets from the Northamptonshire County Council's 
    data distribution website at http://www.northamptonshireanalysis.co.uk.
    The data seems to be organized under the following hierarchy:
        - Themes : Broad themes such as "Population & Census', 'Economy' etc.
        - SubThemes : Themes within each broad theme (e.g. Population/Age/Gender data within 'Population & Census'
        - Dataviews : The actual datasets, each subtheme could have multiple dataviews
        - Geo Ids : The geographical scope of the dataview -- could be county, dictrict etc.
    '''
    def __init__(self):
        self.root_url  = 'http://www.northamptonshireanalysis.co.uk/'

        self.geo_ids = {
            'county' : 28,
            'district' : 46,
            'electoral_division_post_2013' : 67,
            'lsoa' : 58,
            'community_safety_partnership' : 76,
            'ccg_locality' : 49,
            'region' : 22,
        }
        
        self.theme_ids = {
            'Adult Social Care' : 43,
            'Children and Young People' : 47,
            'Community Safety' : 37,
            'Economy' : 10,
            'Education and Skills' : 26,
            'Environment and Living' : 44,
            'Health and Well-being' : 18,
            'Population and Census' : 6,
        }
        
        
        self.re_theme = re.compile(r'^.*fetchChildObjects\(\'DataViews\',event,\'theme_(\d+)\'.*$')
        self.re_view_url = re.compile(r'^\./view\?viewId\=(\d+)$')
    
    def get_dataviews(self, theme_id, dataview_links):
        for link in dataview_links:
            url = unicode(link['href'])
            matchobj = self.re_view_url.match(url)
            if not matchobj is None:
                id = int(matchobj.group(1))
                description = unicode(link['title'])
                title = unicode(link.string)
                yield({ 'id' : id, 'title' : title, 'description' : description })
                
    def get_subtheme(self, subtheme_name, subtheme_id):
        ''' The subtheme page contains a list of links to dataviews, parse them from the HTML
        e.g. 'http://www.northamptonshireanalysis.co.uk/dataviews/rawlist?themeId=XXX'
        '''
        
        # Encode the URL's argument string
        args = urllib.urlencode({'themeId': subtheme_id})
        
        # Make the full URL
        url = self.root_url + 'dataviews/rawlist?' + args
        
        print(url)
        
        # Fetch the contents
        response = urllib2.urlopen(url)
    
        #Make the parser
        soup = BeautifulSoup(response)
        
        #print(soup)
        
        # Find the 'scriptableTreeNode div element that contains the subthemes
        dataview_links = soup.find_all('a')
        
        
        return { 'id' : subtheme_id, 'name' : subtheme_name, 'dataviews' : [ d for d in self.get_dataviews(subtheme_id, dataview_links)]}
        
        # Find all the 'a' element tags -- these contain the actual subtheme descriptions
        #subtheme_links = subtheme_parent.find_all('a')
        
        #return { 'name' : theme_name , 'id' : self.theme_ids[theme_name], 'subthemes' : [s for s in self.get_subthemes(theme_name, subtheme_links)] }
        
    def get_subthemes(self, theme_name, subtheme_links):
        # For each link:
        #     if it contains some embedded text:
        #         it is a subtheme description, so parse it, skip others
        #         The 'onclick' attribute has some javascript that contains the theme id, use a regex to extract it.
        for link in subtheme_links:
            
            text = link.string
            
            onclick = link['onclick']
            
            if not text is None:
                matchobj = self.re_theme.match(onclick)
                if not matchobj is None:
                    subtheme_name = unicode(text)
                    subtheme_id = int(matchobj.group(1))
                    if subtheme_name != theme_name:
                        yield(self.get_subtheme(subtheme_name, subtheme_id)) 
    
    def get_theme(self, theme_name):
        ''' The theme page contains a list of sub-themes, parse them from the HTML
        e.g. 'http://www.northamptonshireanalysis.co.uk/bytheme?themeId=XXX&themeName=YYY'
        '''
        
        # Encode the URL's argument string
        args = urllib.urlencode({'themeId': self.theme_ids[theme_name], 
                                 'themeName': theme_name
                                 })
        
        # Make the full URL
        url = self.root_url + 'bytheme?' + args
        
        # Fetch the contents
        response = urllib2.urlopen(url)
    
        #Make the parser
        soup = BeautifulSoup(response)
        
        # Find the 'scriptableTreeNode div element that contains the subthemes
        subtheme_parent = soup.find('div',{'class':'scriptableTreeNode'})
        
        # Find all the 'a' element tags -- these contain the actual subtheme descriptions
        subtheme_links = subtheme_parent.find_all('a')
        
        return { 'name' : theme_name , 'id' : self.theme_ids[theme_name], 'subthemes' : [s for s in self.get_subthemes(theme_name, subtheme_links)] }
    
    def get_themes(self):
        for name in self.theme_ids.keys():
            yield(self.get_theme(name))
    
    def get_metadata(self):
        
        metadata = {
                        'geo_ids' : [ { 'name' : name, 'id' : self.geo_ids[name] } for name in self.geo_ids],
                        'themes' : [ t for t in fd.get_themes() ],
                    }
        
        return metadata
    
    def to_json(self):
        
        metadata = self.get_metadata()
        
        return json.dumps(metadata, indent=4, separators=[',', ' : '])   

if __name__ == '__main__':
    fd = DataFetcher()
    #metadata = fd.to_json()
    #print(metadata)
    fd.get_subtheme(theme_id=221)