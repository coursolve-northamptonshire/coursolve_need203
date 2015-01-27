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
import os, errno

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
    
        self.metadata = None
        
    def sync_metadata(self):
        self.metadata = self.fetch_metadata()
        
    def load_metadata(self, file_name):
        
        fp = open(file_name, "r")
        
        self.metadata = json.load(fp)
        
        fp.close()
    
    def save_metadata(self, file_name):
        fp = open(file_name, "w")
        
        json.dump(self.metadata, fp, indent=4, separators=[',', ' : '])
        
        fp.close()
        
    def get_dataview_url(self, dataview_id, geo_name):
        args = urllib.urlencode({'viewId' : dataview_id,
                                'geoId' : self.geo_ids[geo_name],
                                'viewer' : 'CSV',
                                })
        csv_url = self.root_url + 'data/csv?' + args
        
        return csv_url
    
    def generate_dataview_ids(self):
        for theme in self.metadata['themes']:
            for subtheme in theme['subthemes']:
                for dataview in subtheme['dataviews']:
                    yield(dataview['id'])
    
    def get_dataview_ids_with_details(self):
        d_dataview = {}
        for theme in self.metadata['themes']:
            for subtheme in theme['subthemes']:
                for dataview in subtheme['dataviews']:
                    d_dataview[dataview['id']] = { 'title' : dataview['title'], 'theme' : theme['name'], 'subtheme' : subtheme['name'], 'description' : dataview['description'], }
        return d_dataview
    
    def get_dataview_ids(self):
        return [ d for d in self.generate_dataview_ids() ]
    
    
    def fetch_dataviews(self, theme_id, dataview_links):
        for link in dataview_links:
            url = unicode(link['href'])
            matchobj = self.re_view_url.match(url)
            if not matchobj is None:
                dv_id = int(matchobj.group(1))
                description = unicode(link['title'])
                title = unicode(link.string)
                 
                yield({ 'id' : dv_id, 'title' : title, 'description' : description, })
                
    def fetch_subtheme(self, subtheme_name, subtheme_id):
        ''' The subtheme page contains a list of links to dataviews, parse them from the HTML
        e.g. 'http://www.northamptonshireanalysis.co.uk/dataviews/rawlist?themeId=XXX'
        '''
        
        # Encode the URL's argument string
        args = urllib.urlencode({'themeId': subtheme_id})
        
        # Make the full URL
        url = self.root_url + 'dataviews/rawlist?' + args
        
        # Fetch the contents
        response = urllib2.urlopen(url)
    
        #Make the parser
        soup = BeautifulSoup(response)
        
        # Find the 'scriptableTreeNode div element that contains the subthemes
        dataview_links = soup.find_all('a')
        
        
        return { 'id' : subtheme_id, 'name' : subtheme_name, 'dataviews' : [ d for d in self.fetch_dataviews(subtheme_id, dataview_links)]}
        
        
    def fetch_subthemes(self, theme_name, subtheme_links):
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
                        yield(self.fetch_subtheme(subtheme_name, subtheme_id)) 
    
    def fetch_theme(self, theme_name):
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
        
        return { 'name' : theme_name , 'id' : self.theme_ids[theme_name], 'subthemes' : [s for s in self.fetch_subthemes(theme_name, subtheme_links)] }
    
    def fetch_themes(self):
        for name in self.theme_ids.keys():
            yield(self.fetch_theme(name))
    
    def fetch_metadata(self):
        
        metadata = {
                        'geo_ids' : [ { 'name' : name, 'id' : self.geo_ids[name] } for name in self.geo_ids ],
                        'themes' : [ t for t in fd.fetch_themes() ],
                    }
        
        return metadata
    
    def to_json(self):
        
        if self.metadata is None:
            self.metadata = self.fetch_metadata()
        
        return json.dumps(self.metadata, indent=4, separators=[',', ' : '])
       
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
    
    def fetch_dataview_csv(self, dv_id, geo_name, verbose=False):
        csv_url = self.get_dataview_url(dv_id, geo_name)
        
        if verbose:
            print("\t<-  " + csv_url)
        try:
            response = urllib2.urlopen(csv_url)
        except:
            print("\tUnable to fetch.")
            return None
        
        return response
        
    def download_dataview_csv(self, dir_name, dv_id, dv_desc, geo_name, verbose=False):
        
        csv_url = self.get_dataview_url(dv_id, geo_name)
        
        if verbose:
            print("\t<-  " + csv_url)
        try:
            response = urllib2.urlopen(csv_url)
        except:
            print("\tUnable to fetch. Skipping...")
            return
        
        dir_name = os.path.join(dir_name, dv_desc['theme'], dv_desc['subtheme'])
        
        try:
            self.mkdir_p(dir_name)
        except:
            print("\tUnable to Save. Skipping...")
            return
        
        
        csv_file_name = os.path.join(dir_name, 'dataview' + '_' + str(dv_id) + '_' + geo_name + '.csv')
        if verbose:
            print("\t->  " + csv_file_name)
        fp = open(csv_file_name, "w")
        fp.write(response.read())
        fp.close()
        
    def download_dataviews(self, dir_name, geo_name, verbose=False):
        for (dv_id, dv_desc) in self.get_dataview_ids_with_details().items():
            if verbose:
                print('Dataview id: ' + str(dv_id))
            self.download_dataview_csv(dir_name, dv_id, dv_desc, geo_name, verbose)
            
    def download_all_dataviews(self, dir_name,verbose=False):
        for geo_name in self.geo_ids.keys():
            self.download_dataviews(dir_name, geo_name, verbose)
            
if __name__ == '__main__':
    fd = DataFetcher()
    #metadata = fd.to_json()
    #print(metadata)
    #fd.sync_metadata()
    #fd.save_metadata('metadata.json')
    fd.load_metadata('metadata.json')
    
    fd.download_all_dataviews('data', verbose=True)