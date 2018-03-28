# Metadata from File by Quinton Reeves

import os, string, hashlib, base64, re, plistlib, unicodedata, datetime, sys, time, locale, ConfigParser
from string import Template

def logdebug(message, *args):
    if bool(Prefs['logger.debug.enabled']):
        Log(message, *args)

def log(message, *args):
    Log(message, *args)

def isblank (string):
    return not(string and string.strip())

def unicodize(s):
    filename = s
    logdebug('before unicodizing: %s', str(filename))
    if os.path.supports_unicode_filenames:
        try: filename = unicode(s.decode('utf-8'))
        except: pass
    logdebug('after unicodizing: %s', str(filename))
    return filename

def addfilepath(filepaths, newfilepath):
    evalpaths = []
    newdirpath = newfilepath
    if os.path.isfile(newdirpath):
        newdirpath = os.path.dirname(newdirpath)
    # determine if the new path is a sub-path or a new path
    logdebug('verifying file path [%s] should be added', newdirpath)
    appendpath = True
    for path in filepaths:
        path = os.path.normpath(os.path.normcase(path))
        logdebug('existing path [%s]', path)
        newdirpath = os.path.normpath(os.path.normcase(newdirpath))
        logdebug('new path [%s]', newdirpath)
        if newdirpath == path:
            logdebug('paths are equivalent - keeping existing path [%s]', path)
            evalpaths.append(path)
            appendpath = False
        elif newdirpath.startswith(path):
            logdebug('path [%s] is a subdirectory of [%s] - keeping new path [%s]', newdirpath, path, newdirpath)
            evalpaths.append(newdirpath)
            appendpath = False
        else:
            logdebug('keeping existing path [%s]', newdirpath)
            evalpaths.append(path)
    # path is a new path - keep it
    if appendpath:
        logdebug('keeping new path [%s]', newdirpath)
        evalpaths.append(newdirpath)
    return evalpaths

def addfilelabel(filelabels, newfilelabels):
    evallabels = []
    if newfilelabels != None and newfilelabels != "":
        evalnewlabels = newfilelabels.split(",")
        for newlabel in evalnewlabels:
            # determine if the new label
            logdebug('verifying file label [%s] should be added', newlabel)
            appendlabel = True
            for label in filelabels:
                if newlabel == label:
                    logdebug('labels are equivalent - keeping existing label [%s]', label)
                    evallabels.append(label)
                    appendlabel = False
                else:
                    logdebug('keeping existing Label [%s]', newlabel)
                    evallabels.append(label)
            # label is a new Label - keep it
            if appendlabel:
                logdebug('keeping new Label [%s]', newlabel)
                evallabels.append(newlabel)
    return evallabels

def findfiles(filepaths, filenames):
    evalfiles = []
    for filepath in filepaths:
        escaped = False
        recursed = 0
        parentdir = filepath
        # Get the parent directory for the file
        if os.path.isfile(filepath):
            parentdir = os.path.dirname(parentdir)
        # iterate over the directory
        while not escaped:
            logdebug('looking in parent directory %s', parentdir)
            # create the file path
            for filename in filenames:
                pathtofind = os.path.normpath(os.path.normcase(os.path.join(parentdir, filename)))
                logdebug('determining whether file %s exists', pathtofind)
                if os.path.exists(pathtofind) and os.path.isfile(pathtofind):
                    logdebug('file %s exists', pathtofind)
                    evalfiles.append(pathtofind);
                else:
                    logdebug('file %s does not exist', pathtofind)
            # go up a directory
            logdebug('going up a directory')
            newdir = os.path.abspath(os.path.dirname(parentdir))
            logdebug('new directory path %s', newdir)
            # if the new directory and parent directory are the same then we have reached the top directory - stop looking for the file
            if newdir == parentdir:
                logdebug('root directory %s found - stopping directory traversal', newdir)
                escaped = True
            else:
                recursed = recursed + 1
                if recursed > int(Prefs['mdf.directory.recurse']):
                    logdebug('stopping at %s - maximum recursions reached', newdir)
                    escaped = True
                else:
                    parentdir = newdir
    return evalfiles

def findmoviefile(filepaths, filenames):
    filepath = None
    logdebug('looking for files with names %s in path list %s', str(filenames), str(filepaths))
    filepath = findfiles(filepaths, filenames)
    if not filepath:
        logdebug('movie metadata file not found')
    return filepath

def getmetadatafilename():
    fileext = Prefs['mdf.metadata.filename']
    if isblank(fileext):
        fileext = '_metadata'
    logdebug('using metadata file: %s', fileext)
    return fileext

class customparsermetadata(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = ConfigParser.SafeConfigParser()
        self.metadata.read(filepath)

    def get(self, name):
        try:
            return self.metadata.get('metadata', name)
        except:
            return None

def getcatalogfilename():
    fileext = Prefs['mdf.catalog.filename']
    if isblank(fileext):
        fileext = '_catalog'
    logdebug('using catalog file: %s', fileext)
    return fileext

class customparsercatalog(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = ConfigParser.SafeConfigParser()
        self.metadata.read(filepath)

    def catalog(self):
        return self.metadata

    def get(self, section, name):
        try:
            return self.metadata.get(section, name)
        except:
            return None

class metadatafileagent(Agent.Movies):
    name = "Metadata File"
    languages = Locale.Language.All()
    primary_provider = True
    accepts_from = ['com.plexapp.agents.none', 'com.plexapp.agents.localmedia']
    contributes_to = accepts_from
    fallback_agent = ['com.plexapp.agents.none']

    def search(self, results, media, lang):
        logdebug('media id: %s', media.id)
        logdebug('media file name: %s', str(media.filename))
        logdebug('media primary metadata: %s', str(media.primary_metadata))
        logdebug('media primary agent: %s', str(media.primary_agent))
        logdebug('media title: %s', str(media.title))
        logdebug('media name: %s', str(media.name))
        # Compute the GUID based on the media hash.
        try:
            part = media.items[0].parts[0]
            filename = unicodize(part.file)
            logdebug('part file name: %s', filename)
        except:
            logdebug('part does not exist')
        results.Append(MetadataSearchResult(id=media.id, name=media.name, score=100))

    def update(self, metadata, media, lang):
        logdebug('meta data agent object id: %s', id(self))
        logdebug('metadata: %s', str(metadata))
        logdebug('media: %s', str(media))
        logdebug('lang: %s', str(lang))
        # set the metadata title
        metadata.title = media.title
        # list of series parsers
        filepaths = []
        filename = None
        for item in media.items:
            for part in item.parts:
                if filename == None:
                    filename = part.file;
                logdebug('item file path: %s', part.file)
                absfilepath = os.path.abspath(unicodize(part.file))
                logdebug('absolute file path: %s', absfilepath)
                filepaths = addfilepath(filepaths, absfilepath)
        if filename == None:
            filename = media.items[0].parts[0].file;
        log('metadata file scan: %s (%s)', media.title, filename)
        age = None
        year = None
        rating = None
        title = None
        studio = None
        tagline = None
        summary = None
        trivia = None
        quotes = None
        genres = []
        writers = []
        directors = []
        producers = []
        countries = []
        collections = []
        if bool(Prefs['mdf.metadata.enabled']):
            logdebug('use metadata file option is enabled - extracting metadata from metadata files')
            metadatafile = getmetadatafilename()
            metadatafilepath = findmoviefile(filepaths, [filename + '.ini', metadatafile])
            for filepath in metadatafilepath:
                log('reading metadata file: %s', filepath)
                filemetadata = customparsermetadata(filepath)
                if age == None:
                    age = filemetadata.get('content_rating_age')
                if year == None:
                    year = filemetadata.get('year')
                if rating == None:
                    rating = filemetadata.get('content_rating')
                if title == None:
                    title = filemetadata.get('title')
                if studio == None:
                    studio = filemetadata.get('studio')
                if tagline == None:
                    tagline = filemetadata.get('tagline')
                if summary == None:
                    summary = filemetadata.get('summary')
                if trivia == None:
                    trivia = filemetadata.get('trivia')
                if quotes == None:
                    quotes = filemetadata.get('quotes')
                genres = addfilelabel(genres, filemetadata.get('genres'))
                writers = addfilelabel(writers, filemetadata.get('writers'))
                directors = addfilelabel(directors, filemetadata.get('directors'))
                producers = addfilelabel(producers, filemetadata.get('producers'))
                countries = addfilelabel(countries, filemetadata.get('countries'))
                collections = addfilelabel(collections, filemetadata.get('collections'))
        if bool(Prefs['mdf.catalog.enabled']):
            logdebug('use catalog file option is enabled - extracting metadata from catalog files')
            catalogfile = getcatalogfilename()
            catalogfilepath = findmoviefile(filepaths, [catalogfile])
            for filepath in catalogfilepath:
                log('reading catalog file: %s', filepath)
                filetitle = re.sub(" \(.\)$", "", media.title);
                filecatalog = customparsercatalog(filepath)
                filecatalogitems = filecatalog.catalog()
                for section in filecatalogitems.sections():
                    if re.search(section, filetitle):
                        if age == None:
                            age = filecatalog.get(section, 'content_rating_age')
                        if year == None:
                            year = filecatalog.get(section, 'year')
                        if rating == None:
                            rating = filecatalog.get(section, 'content_rating')
                        if title == None:
                            title = filecatalog.get(section, 'title')
                        if studio == None:
                            studio = filecatalog.get(section, 'studio')
                        if tagline == None:
                            tagline = filecatalog.get(section, 'tagline')
                        if summary == None:
                            summary = filecatalog.get(section, 'summary')
                        if trivia == None:
                            trivia = filecatalog.get(section, 'trivia')
                        if quotes == None:
                            quotes = filecatalog.get(section, 'quotes')
                        genres = addfilelabel(genres, filecatalog.get(section, 'genres'))
                        writers = addfilelabel(writers, filecatalog.get(section, 'writers'))
                        directors = addfilelabel(directors, filecatalog.get(section, 'directors'))
                        producers = addfilelabel(producers, filecatalog.get(section, 'producers'))
                        countries = addfilelabel(countries, filecatalog.get(section, 'countries'))
                        collections = addfilelabel(collections, filecatalog.get(section, 'collections'))
        if age != None:
            metadata.content_rating_age = int(age)
            log('content_rating_age: %s', age)
        if year != None:
            metadata.year = int(year)
            log('content_rating_year: %s', year)
        if rating != None:
            metadata.content_rating = rating
            log('content_rating: %s', rating)
        if title != None:
            metadata.title = title
            log('title: %s', title)
        if studio != None:
            metadata.studio = studio
            log('studio: %s', studio)
        if tagline != None:
            metadata.tagline = tagline
            log('tagline: %s', tagline)
        if summary != None:
            metadata.summary = summary
            log('summary: %s', summary)
        if trivia != None:
            metadata.trivia = trivia
            log('trivia: %s', trivia)
        if quotes != None:
            metadata.quotes = quotes
            log('quotes: %s', quotes)
        if genres:
            metadata.genres.clear()
            for label in genres:
                metadata.genres.add(label)
            log('genres: %s', genres)
        if writers:
            metadata.writers = writers
            log('writers: %s', writers)
        if directors:
            metadata.directors = directors
            log('directors: %s', directors)
        if producers:
            metadata.producers = producers
            log('producers: %s', producers)
        if countries:
            metadata.countries = countries
            log('countries: %s', countries)
        if collections:
            metadata.tags = collections
            metadata.collections = collections
            log('collections: %s', collections)

def Start():
    log('starting agents %s, %s', "Metadata File")
    pass
