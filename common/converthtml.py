from tabulate import tabulate

class ConvertHTML:
    def __init__(self) -> None:
        pass

    def get_h1(self, str_subject):
        return '<h1 align="center" style="color:black;font-family:consolas;">' + str_subject + '</h1>'

    def get_h2(self, str_subject):
        return '<h2 style="color:black;font-family:consolas;padding-left:10%">' + str_subject + '</h2>'

    def get_h3(self, str_subject):
        return '<h3 style="color:black;font-family:consolas;padding-left:10%">' + str_subject + '</h3>'

    def get_h4(self, str_subject):
        return '<h4 align="center" style="color:black;font-family:consolas;">' + str_subject + '</h4>'

    def get_h5(self, str_subject):
        return '<h5 style="color:black;font-family:consolas;">' + str_subject + '</h5>'

    def get_h6(self, str_subject):
        return '<h6 style="color:black;font-family:consolas;">' + str_subject + '</h6>'

    def get_p(self, str_subject):
        return f'<p style="color:black;font-family:consolas;font-size:100%;padding-left:15%">' + str_subject + '</p>'

    def get_p_highlight(self, str_subject):
        return f'<p style="color:red;font-family:consolas;font-size:100%;padding-left:15%">' + str_subject + '</p>'

    def get_newline(self):
        return '<br>'

    def get_da_table(self, data):
        table_html = tabulate(data, headers=["ChannelName", "Device", "Placement"], tablefmt="html")
        result = table_html.replace('<table>', '<table border="1" align="center" cellpadding="2" cellspacing="0" style="color:black;font-family:consolas;text-align:center; width:80%;">')        
        return result
from tabulate import tabulate

class ConvertHTML:
    def __init__(self) -> None:
        pass

    def get_h1(self, str_subject):
        return '<h1 align="center" style="color:black;font-family:consolas;">' + str_subject + '</h1>'

    def get_h2(self, str_subject):
        return '<h2 style="color:black;font-family:consolas;padding-left:10%">' + str_subject + '</h2>'

    def get_h3(self, str_subject):
        return '<h3 style="color:black;font-family:consolas;padding-left:10%">' + str_subject + '</h3>'

    def get_h4(self, str_subject):
        return '<h4 align="center" style="color:black;font-family:consolas;">' + str_subject + '</h4>'

    def get_h5(self, str_subject):
        return '<h5 style="color:black;font-family:consolas;">' + str_subject + '</h5>'

    def get_h6(self, str_subject):
        return '<h6 style="color:black;font-family:consolas;">' + str_subject + '</h6>'

    def get_p(self, str_subject):
        return f'<p style="color:black;font-family:consolas;font-size:100%;padding-left:15%">' + str_subject + '</p>'

    def get_p_highlight(self, str_subject):
        return f'<p style="color:red;font-family:consolas;font-size:100%;padding-left:15%">' + str_subject + '</p>'

    def get_newline(self):
        return '<br>'

    def get_da_table(self, data):
        table_html = tabulate(data, headers=['날짜', '기사제목', '작성자', 'Url'], tablefmt="html")
        result = table_html.replace('<table>', '<table border="1" align="center" cellpadding="2" cellspacing="0" style="color:black;font-family:consolas;text-align:center; width:80%;">')        
        return result
