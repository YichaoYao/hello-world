import pandas
from collections import defaultdict
from typing import Iterable, List, TypeVar
import requests
import pdfkit



T = TypeVar("T")

def sortByPriorityList(values: Iterable[T], priority: List[T]) -> List[T]:
    """
    Sorts an iterable according to a list of priority items.
    Usage:
    >>> sort_by_priority_list(values=[1,2,2,3], priority=[2,3,1])
    [2, 2, 3, 1]
    >>> sort_by_priority_list(values=set([1,2,3]), priority=[2,3])
    [2, 3, 1]
    """
    priority_dict = defaultdict(
        lambda: len(priority), zip(priority, range(len(priority)),),
    )
    priority_getter = priority_dict.__getitem__  # dict.get(key)
    return sorted(values, key=priority_getter)


def writeToHTML(df, title='', filename='out.html', address = ""):
    '''
    Write an entire dataframe to an HTML file with nice formatting.
    '''

    result = '''
<html>
<head>
<style>

    h2 {
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
    }
    table { 
        margin-left: auto;
        margin-right: auto;
    }
    table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
    }
    th, td {
        padding: 5px;
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 90%;
    }
    table tbody tr:hover {
        background-color: #dddddd;
    }
    .wide {
        width: 90%; 
    }

</style>
</head>
<body>
    '''
    result += '<h2> %s </h2>\n' % title
    result += df.to_html(classes='wide', escape=False, index = False)
    result += f'<p> {address} <p>'
    result += '''
</body>
</html>
'''
    with open(filename, 'w') as f:
        f.write(result)

def generateMailInformation(to_be_shipped):
    for package_id in to_be_shipped["Package ID"].unique():
        package_df = to_be_shipped[to_be_shipped["Package ID"] == package_id]
        address = to_be_shipped["Address"][0]
        package_df = package_df[["Package ID", "Card Name", "Set Name", "Condition", "Finish"]]

        
        html = f"{package_id}.html"
        pdf = f"{package_id}.pdf"
        
        writeToHTML(package_df, "Trade Details", f"{package_id}.html", address)

        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }

        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        pdfkit.from_file(html, pdf, options = options, configuration=config)

def processTag(tags):
    output = []
    priority_list = ["MC", "Land", "U", "G", "B", "R", "W"]

    tags = sortByPriorityList(tags, priority_list)
    if "0_Verified" not in tags :
        output.append("Not_Verified")
    for tag in tags:
        if tag not in ["0", "1", "2", "3", "4", "5", "5+", "0_Verified"]:
            if "0_Verified" not in tags :
                return tag + "_not_verified"
            else:
                return tag 

def getCardImages(to_be_shipped):
    image = "search_list.html"
    htmlfile = open(image, "w")

    for group in to_be_shipped["Tags"].unique():
        group_df = to_be_shipped[to_be_shipped["Tags"] == group]

        htmlfile.write(f"<p><strong><span style=\"font-size: 20px;\">Group: {group}</span></strong></p>")
        for index, row in group_df.iterrows():
            card_name = row["Card Name"]
            set_name = row["Set Name"]
            foil = row["Finish"]
            condition = row["Condition"]
            package = row["Package ID"]
            url = f"https://www.multiversebridge.com/api/v1/cards/search?name={card_name}"
            response = requests.get(url)
            #print(card_name + " " + set_name)
            htmlfile.write(f"<p><input type=\"checkbox\"><strong>{card_name}&nbsp; {set_name} &nbsp; {foil}-{condition} &nbsp; Package:{package}</strong></p>")
            data = response.json()
            for card in data:
                if card["edition"] == set_name:
                    card_id = card["scryfall_id"]
                    url = f"https://api.scryfall.com/cards/{card_id}"
                    response = requests.get(url)
                    data = response.json()
                    if "card_faces" in data.keys():
                        htmlfile.write('</p>')
                        for face in data["card_faces"]:
                            image_uri = face["image_uris"]["normal"]
                            htmlfile.write(f'<img src="{image_uri}" height="400">')
                        htmlfile.write('</p>')
                    else:
                        image_uri = data["image_uris"]["normal"]
                        htmlfile.write(f'<p><img src="{image_uri}" height="400"></p>')
                    break



df = pandas.read_csv("send.csv")
to_be_shipped = df[df["State"].str.contains("Committed")]
to_be_shipped["Tags"] = to_be_shipped["Tags"].str.split(', ', expand=False)
to_be_shipped["Tags"] = to_be_shipped["Tags"].apply(processTag)

getCardImages(to_be_shipped)
#generateMailInformation(to_be_shipped)
