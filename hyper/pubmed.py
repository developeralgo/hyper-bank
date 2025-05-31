import json
from datetime import datetime
import requests as r
from lxml import etree



def fetch_article_by_pmid(pmid ,api_key):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",  # You can use "json" if needed
        "api_key": api_key
    }
    
    response = r.get(base_url, params=params)
    if response.status_code != 200:
        print(f"Error fetching article with PMID {pmid}: {response.status_code}")
        return None
    else:
        return response.text

    
    



def search_pubmed(search_query, api_key,history=False  ,start_date=None, end_date=None,):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # Set search parameters with usehistory enabled
    params = {
        "db": "pubmed",
        "term": f"('{search_query}'[Title]) AND ('systematic review'[Publication Type] OR meta-analysis[Publication Type])", 
        "retmode": "json",
        "retmax": 500,  # Number of results per batch
        "api_key": api_key  # Use API key to increase limits
    }
    if history==True:
        params["usehistory"]="y"

    if start_date and end_date:
        try:
            # Format dates to YYYY/MM/DD for Entrez API
            start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y/%m/%d")
            end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y/%m/%d")

            # Correct date parameter usage for esearch
            params["term"] += f" AND ('{start_date_formatted}'[Date - Publication] : '{end_date_formatted}'[Date - Publication])"
            #Remove the old date parameters
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return None, None, None, None


    response = r.get(base_url, params=params)
    print(response.text)
    response_data = response.json()
    print(response_data)


    # Extract WebEnv and QueryKey for later retrieval
    webenv = response_data["esearchresult"].get("webenv")
    query_key = response_data["esearchresult"].get("querykey")
    count = int(response_data["esearchresult"].get("count", 0))
    idlist = response_data["esearchresult"].get("idlist")
    translationSet = "" 
    if response_data["esearchresult"].get("translationset")== [] :
        translationSet = ""
    else:
             translationSet = response_data["esearchresult"].get("translationset")[0]["from"] + "-" + response_data["esearchresult"].get("translationset")[1]["to"]
    queryTranslation = response_data["esearchresult"].get("querytranslation")

    if not webenv or not query_key:
        print("Error retrieving WebEnv or QueryKey.")
        return None
    
    result =  {"query":search_query,
            "webenv":webenv,
            "query_key":query_key,
            "count": count,
            "idlist":idlist,
            "translationset":"",
            "translation_set":translationSet,
            "query_translation":queryTranslation,
            "fetched":False,
            "saved":True}
    response = r.post("http://localhost:3001/SaveSearchResult",json=result)
    if response.status_code != 201:
        print("Error saving search result in the database")
        result["saved"] = False
        return  result
    else:
        result["saved"] = True
        return result




######################################################################################################################


def fetch_batch(webenv, query_key,api_key ,  retstart=0, retmax=500,file_path=None):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retmode": "xml",  # You can use "json" if needed, but XML is more detailed
        "retstart": retstart,  # Offset for pagination
        "retmax": retmax,  # Number of results per batch
        "api_key": api_key
    }
    
    
    response = r.get(base_url, params=params)
    print(response.status_code)
    print(response.text)
   

    
    try:
        if file_path is None:
            file_path = f"~/Downloads/{webenv}.xml"
        file_path = f"./batches/{webenv}.xml"
        with open(file_path, "w") as file:
            file.write(response.text)

            return {"batch_id": webenv, "saved":True, "file_path":file_path}
    except:
        print("Error writing file")
        return {"batch_id": webenv,"saved":False, "file_path":None,"xml":response.text}

######################################################################################################################


def parse_pubmed_article_set(xml_data):
    # Parse the XML data
    root = etree.fromstring(xml_data.encode('utf-8'))
    
    articles = []
    # Iterate through each PubmedArticle in the PubmedArticleSet
    for article in root.xpath("//PubmedArticle"):

        article_data = {}
        article_data['pmid'] = ""
        article_data['doi'] = ""
        article_data['pii'] = ""
        article_data['pmc'] = ""
        for item in article.findall(".//ArticleId"):
            if item.get("IdType") == "pubmed":
                article_data['pmid'] = item.text
            else:
                article_data[item.get("IdType")] = item.text
        article_data['journalTitle'] = article.find(".//Journal/Title").text or None
        article_data["journalAbbreviation"] = article.find(".//Journal/ISOAbbreviation").text or None

        volume = article.find("./MedlineCitation/Article/Journal/JournalIssue/Volume")
        issue = article.find("./MedlineCitation/Article/Journal/JournalIssue/Issue")
        PubYear = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year")
        PubMonth = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Month")
        PubDay = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Day")


        article_data['volume'] = volume.text if volume is not None else None
        article_data['issue'] = issue.text if issue is not None else None
        article_data['publication_year'] = PubYear.text if PubYear is not None else None
        article_data['publication_month'] = PubMonth.text if PubMonth is not None else None
        article_data['publication_day'] = PubDay.text if PubDay is not None else None

        article_data["electronic_issn"] = ""
        article_data["print_issn"] = ""
        for element in (article.findall(".//ISSN")):
                if element.get("IssnType") == "Print":
                    article_data['print_issn'] = element.text
                if element.get("IssnType") == "Electronic":
                    article_data['electronic_issn'] = element.text

        medline = article.find(".//MedlineJournalInfo")
        medline_country = article.find(".//MedlineJournalInfo/Country")
        article_data['medline_country'] = medline_country.text if medline_country is not None else None
        article_data['medline_ta'] = medline.find(".//MedlineTA").text if medline.find(".//MedlineTA") is not None else None
        article_data['nlm_unique_id'] = medline.find(".//NlmUniqueID").text if medline.find(".//NlmUniqueID") is not None else None
        article_data['issn_linking'] = medline.find(".//ISSNLinking").text if medline.find(".//ISSNLinking") is not None else None
        # for child in medline:
        #     article_data[child.tag] = child.text

        ## Extracting Journal Info
        

        article_data['articleTitle'] = article.find(".//ArticleTitle").text
        article_data['abstract'] = " ".join(article.xpath(".//Abstract//AbstractText/text()")) or None

        
        mesh_headings = []
        for mesh in article.xpath(".//MeshHeadingList/MeshHeading"):
            descriptor_name = mesh.xpath("./DescriptorName/text()")[0]
            mesh_headings.append(str(descriptor_name))
        
        article_data['meshHeadings'] = mesh_headings
        key_words = []
        keys = article.findall(".//Keyword")
        if keys is not None:
            for element in keys:
                key_words.append(element.text)
        article_data['keywords'] = key_words
        article_data["pub_type"] = article.xpath("./MedlineCitation/Article/PublicationTypeList/PublicationType/text()")
        
        
        
        authors = []
        for author in article.xpath("./MedlineCitation/Article/AuthorList/Author"):
            if author is not None:
                author_info = {
                    'last_name': str(author.xpath("./LastName/text()")[0]) if author.xpath("./LastName/text()") else None,
                    'first_name': str(author.xpath("./ForeName/text()")[0]) if author.xpath("./ForeName/text()") else None,
                    'affiliation': str(author.xpath("./AffiliationInfo/Affiliation/text()")[0]) if author.xpath("./AffiliationInfo/Affiliation/text()") else None
                }
                authors.append(author_info)
        article_data['authors'] = authors
        
        
        


        articles.append(article_data)
    
    return articles


###########################333333333
def parse_singel_article(xml_data):
    tree = etree.fromstring(xml_data.encode('utf-8'))
    article = tree.xpath("//PubmedArticle")[0]
    article_data = {}
    article_data['pmid'] = ""
    article_data['doi'] = ""
    article_data['pii'] = ""
    article_data['pmc'] = ""
    for item in article.findall(".//ArticleId"):
        if item.get("IdType") == "pubmed":
            article_data['pmid'] = item.text
        else:
            article_data[item.get("IdType")] = item.text
    article_data['journalTitle'] = article.find(".//Journal/Title").text or None
    article_data["journalAbbreviation"] = article.find(".//Journal/ISOAbbreviation").text or None

    volume = article.find("./MedlineCitation/Article/Journal/JournalIssue/Volume")
    issue = article.find("./MedlineCitation/Article/Journal/JournalIssue/Issue")
    PubYear = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year")
    PubMonth = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Month")
    PubDay = article.find("./MedlineCitation/Article/Journal/JournalIssue/PubDate/Day")


    article_data['volume'] = volume.text if volume is not None else None
    article_data['issue'] = issue.text if issue is not None else None
    article_data['publication_year'] = PubYear.text if PubYear is not None else None
    article_data['publication_month'] = PubMonth.text if PubMonth is not None else None
    article_data['publication_day'] = PubDay.text if PubDay is not None else None

    article_data["electronic_issn"] = ""
    article_data["print_issn"] = ""
    for element in (article.findall(".//ISSN")):
            if element.get("IssnType") == "Print":
                article_data['print_issn'] = element.text
            if element.get("IssnType") == "Electronic":
                article_data['electronic_issn'] = element.text

    medline = article.find(".//MedlineJournalInfo")
    medline_country = article.find(".//MedlineJournalInfo/Country")
    article_data['medline_country'] = medline_country.text if medline_country is not None else None
    article_data['medline_ta'] = medline.find(".//MedlineTA").text if medline.find(".//MedlineTA") is not None else None
    article_data['nlm_unique_id'] = medline.find(".//NlmUniqueID").text if medline.find(".//NlmUniqueID") is not None else None
    article_data['issn_linking'] = medline.find(".//ISSNLinking").text if medline.find(".//ISSNLinking") is not None else None
    # for child in medline:
    #     article_data[child.tag] = child.text

    ## Extracting Journal Info
    

    article_data['articleTitle'] = article.find(".//ArticleTitle").text
    article_data['abstract'] = " ".join(article.xpath(".//Abstract//AbstractText/text()")) or None

    
    mesh_headings = []
    for mesh in article.xpath(".//MeshHeadingList/MeshHeading"):
        descriptor_name = mesh.xpath("./DescriptorName/text()")[0]
        mesh_headings.append(str(descriptor_name))
    
    article_data['meshHeadings'] = mesh_headings
    key_words = []
    keys = article.findall(".//Keyword")
    if keys is not None:
        for element in keys:
            key_words.append(element.text)
    article_data['keywords'] = key_words
    article_data["pub_type"] = article.xpath("./MedlineCitation/Article/PublicationTypeList/PublicationType/text()")
    
    
    
    authors = []
    for author in article.xpath("./MedlineCitation/Article/AuthorList/Author"):
        if author is not None:
            author_info = {
                'last_name': str(author.xpath("./LastName/text()")[0]) if author.xpath("./LastName/text()") else None,
                'first_name': str(author.xpath("./ForeName/text()")[0]) if author.xpath("./ForeName/text()") else None,
                'affiliation': str(author.xpath("./AffiliationInfo/Affiliation/text()")[0]) if author.xpath("./AffiliationInfo/Affiliation/text()") else None
            }
            authors.append(author_info)
    article_data['authors'] = authors

    return article_data