import mysql.connector as mc
from flask import *
from datetime import datetime
from datetime import timedelta

app = Flask(__name__,
			template_folder = "./templates")



# search route
@app.route("/searching", methods = ["POST"])
def searching():
	form = request.form
	value = form.get('search')
	
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library')
	if value:
		sql ='''SELECT BOOK.Isbn, BOOK.Title, AUTHORS.Name FROM BOOK ,AUTHORS,BOOK_AUTHORS
						WHERE BOOK.Isbn = BOOK_AUTHORS.Isbn AND AUTHORS.Author_id = BOOK_AUTHORS.Author_id
						AND BOOK.Title LIKE '%'''+value+'''%' 
						UNION
						SELECT BOOK.Isbn, BOOK.Title, AUTHORS.Name FROM BOOK ,AUTHORS,BOOK_AUTHORS
						WHERE BOOK.Isbn = BOOK_AUTHORS.Isbn AND AUTHORS.Author_id = BOOK_AUTHORS.Author_id
						AND AUTHORS.Name LIKE '%'''+value+'''%'
						UNION
						SELECT BOOK.Isbn, BOOK.Title, AUTHORS.Name FROM BOOK ,AUTHORS,BOOK_AUTHORS
						WHERE BOOK.Isbn = BOOK_AUTHORS.Isbn AND AUTHORS.Author_id = BOOK_AUTHORS.Author_id
						AND BOOK.Isbn = \''''+value+'''\' 
						'''
		cursor.execute(sql);
		data = cursor.fetchall()
		t = tuple(data)
		column = []
		datas = []
		for row in list(set(t)):
			column.append(row[0])
		tmp = set(column)
		for element in tmp:
			newObj ={
						'Isbn': element,
						'Title': '',
						'Author': '',
						'Status': '',
						}
			datas.append(newObj)
		for row in list(set(t)):
			for data in datas:	
				if(row[0]==data['Isbn']):
					data['Title'] =row[1]
					if(data['Author']):
						data['Author'] =data['Author']+', '+row[2]
					else:
						data['Author'] =row[2]
		# print (datas)
		for data in datas:
			cursor.execute('''SELECT Isbn FROM BOOK_LOANS WHERE Isbn = \''''+data['Isbn']+'''\' AND Date_in IS Null;''')
			result = cursor.fetchall()
			if result:
				data['Status'] ='Not Available'
			else:
				data['Status'] ='Available'
		# print(datas)
		return render_template("search.html", result = datas)
	else:
		return render_template("search.html")
	db.commit()
	db.close()

def update_fine():
		date_today = datetime.now()
		db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
		cursor = db.cursor()
		cursor.execute('USE Library;')
		cursor.execute('DELETE FROM FINES WHERE Paid = 0;')
		cursor.execute('SELECT * FROM BOOK_LOANS;')
		result = cursor.fetchall()
		for line in result:
			date_in = line[5]
			due_date = line[4]
			
			if date_in:
				if date_in > due_date:
					diff_day = (datetime.strptime(str(date_in),'%Y-%m-%d') - datetime.strptime(str(due_date),'%Y-%m-%d')).days	
					Total_fine = diff_day * 0.25
					insertsql = 'INSERT IGNORE INTO FINES VALUES(%s,%s,%s);'
					cursor.execute(insertsql,(line[0],Total_fine,0))
					db.commit()	
			else:
				if(date_today.date() >due_date):
					diff_day = (date_today - datetime.strptime(str(due_date),'%Y-%m-%d')).days
					Total_fine = diff_day * 0.25
					insertsql = 'INSERT IGNORE INTO FINES VALUES(%s,%s,%s);'
					cursor.execute(insertsql,(line[0],Total_fine,0))
					db.commit()
		cursor.close()
		db.close()

def fine_list():
		update_fine()
		results = []
		db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
		cursor = db.cursor()
		cursor.execute('USE Library;')
		cursor.execute('''SELECT C.Card_id , B.Bname ,SUM(F.Fine_amt) FROM BOOK_LOANS AS C ,BORROWER AS B, FINES AS F
				WHERE C.Loan_id = F.Loan_id AND
				B.Card_id = C.Card_id	AND 
				F.Paid = 0	AND 
				F.Fine_amt > 0 GROUP BY C.Card_id''')
		result = cursor.fetchall()
		for loan in result:
			newLoan={
				'card_id':loan[0],
				'name':loan[1],
				'fine':str(loan[2])
				}
			results.append(newLoan)
		cursor.close()
		db.close()
		return results

def pay_fine(card_id):	
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library;')
	cursor.execute('''SELECT Loan_id FROM BOOK_LOANS WHERE Card_id =\''''+card_id+'''\'
		AND Date_in IS NOT NULL;''')
	payed = cursor.fetchall()
	print("payed: ", payed)
	for pay in payed:
		cursor.execute('UPDATE FINES SET Paid = 1 WHERE Loan_id ='+str(pay[0])+'')
	cursor.execute('''SELECT B.Loan_id FROM BOOK_LOANS AS B, FINES AS F
		WHERE Card_id =\''''+card_id+'''\' AND
		B.Loan_id = F.Loan_id AND
		F.Paid = 0	AND 
		B.Date_in IS NULL''')
	not_pay = cursor.fetchall()
	print("not_pay: ", not_pay)
	db.commit()
	cursor.close()
	db.close()
	if not_pay:
		return False
	else:
		return True
		
@app.route("/checkin_search", methods = ["POST"])
def checkin_search():
	form = request.form
	isbn_check = form.get('Isbn')
	cardid_check = form.get('Card_id')
	name_check = form.get('Name')
	print(isbn_check)
	print(cardid_check)
	print(name_check)
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library')
	check_in_list =[]
	insertsql=''
	# if(len(cardid_check)!=6):
	# 	cardid_check =''
	if(len(name_check)==0):
		if(len(isbn_check)!=0):
			insertsql ='''
			SELECT * FROM BOOK_LOANS WHERE Isbn = \''''+isbn_check+'''\' AND Date_in IS NULL
			UNION
			SELECT * FROM BOOK_LOANS WHERE Card_id =\''''+cardid_check+'''\' AND Date_in IS NULL;
			'''
		else:
			insertsql ='''
			SELECT * FROM BOOK_LOANS WHERE Card_id =\''''+cardid_check+'''\' AND Date_in IS NULL;
			'''
	else:		
		if(len(isbn_check)!=0):
			insertsql='''
			SELECT * FROM BOOK_LOANS WHERE Isbn = \''''+isbn_check+'''\' AND Date_in IS NULL
			UNION
			SELECT * FROM BOOK_LOANS WHERE Card_id =\''''+cardid_check+'''\' AND Date_in IS NULL
			UNION
			SELECT * FROM BOOK_LOANS WHERE Card_id IN (SELECT Card_id FROM BORROWER WHERE
			Bname LIKE '%'''+name_check+'''%') AND Date_in IS NULL;
			'''
		else:
			insertsql='''
			SELECT * FROM BOOK_LOANS WHERE Card_id IN (SELECT Card_id FROM BORROWER WHERE
			Bname LIKE '%'''+name_check+'''%') AND Date_in IS NULL;
			'''	
	if(insertsql !=''):		
		print(insertsql)
		cursor.execute(insertsql)
		result = cursor.fetchall()
		print(result)
		if((result)):
			for line in result:
				ableCheckIn ={
								'Title':'',
								'Isbn':line[1],
								'Borrower':'',
								'Card_id':str(line[2]),
								'Dateout':line[3].strftime("%Y-%m-%d"),
								'DueDate':line[4].strftime("%Y-%m-%d"),
							}
				check_in_list.append(ableCheckIn)
			for element in check_in_list:
				cursor.execute('''SELECT * FROM BOOK WHERE Isbn = \''''+element['Isbn']+'''\' ;''')
				result = cursor.fetchall()
				for line in result:
					element['Title'] = line[1]
				cursor.execute('''SELECT Bname FROM BORROWER WHERE BORROWER.Card_id  =\''''+element['Card_id']+'''\';''')
				borrower = cursor.fetchall()	
				element['Borrower'] = borrower[0][0]
				
			return render_template("checkin.html", result = check_in_list)
		else:
			return render_template("message.html", msg = "This person didn't checkout any book.")
	else:	
		return render_template("message.html", msg = "something go wrong with checkin search")	
	cursor.close()
	db.close()

@app.route("/checkout<Isbn>", methods=["GET", "POST"])
def checkout(Isbn):
	isbn = Isbn
	form = request.form
	card = form.get('card_id')
	Date_out = datetime.now() + timedelta(days = 0)
	Due_date = datetime.now() + timedelta(days= 14)
	if(not book_check(card)):
		print("book_check fail!")
	if(not validIsbn(isbn)):
		print("validIsbn fail!")
	if(not book_availiable(isbn)):
		print("book_availiable fail!")
	if(not validcard(card)):
		print("validcard fail!")
	if(book_check(card) and validIsbn(isbn) and book_availiable(isbn) and validcard(card)):
		db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
		cursor = db.cursor()
		cursor.execute('USE Library;')
		insertsql ='''INSERT INTO BOOK_LOANS (Isbn,Card_id,Date_out,Due_date) VALUES(%s,%s,%s,%s);'''
		cursor.execute(insertsql,([isbn,card,Date_out,Due_date]))
		db.commit()
		cursor.close()
		db.close()
		return render_template("message.html", msg ='Checked out successfully!')
	else:	
		return render_template("message.html", msg ='All field is required and valid value')
	
def validIsbn(isbn):	
	if(len(isbn)==10):
		db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
		cursor = db.cursor()
		cursor.execute('USE Library;')
		cursor.execute('SELECT * FROM BOOK WHERE Isbn = \''+isbn+'\';')
		result = cursor.fetchall()
		if(result):
			return True
		else:
			return False			
	else:
		return False

def book_check(card_id):
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library;')
	cursor.execute('''SELECT * FROM BOOK_LOANS WHERE Card_id =\''''+card_id+'''\' AND Date_in IS NULL;''')
	result = cursor.fetchall()
	count = len(result)
	cursor.close()
	db.close()
	if (count < 3 ):
		return True
	else:	
		print('Error Message', 'Maximum books to checkout is only three,please checkin books to restore this service')
		return False

def book_availiable(isbn):
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library;')
	cursor.execute('''SELECT * FROM BOOK_LOANS WHERE Isbn =\''''+isbn+'''\'AND Date_in IS NULL;''')
	result = cursor.fetchall()
	count = len(result)
	cursor.close()
	db.close()
	if (count > 0):
		return False
	else:
		return True
	

def validcard(card):	
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library;')
	cursor.execute('''SELECT * FROM BORROWER WHERE Card_id =\''''+card+'''\';''')
	result = cursor.fetchall()
	count = len(result)
	cursor.close()
	db.close()
	if (count > 0 ):
		return True
	else:
		print('Error Message', 'Cannnot find your ID , please register before checkout')
		return False
# btn functions
@app.route("/btn_checkout_entry<Isbn>", methods=["GET"])
def btn_checkout_entry(Isbn):
	if(book_availiable(Isbn)):
		return render_template("checkout.html", Isbn= Isbn)
	else:
		return render_template("message.html", msg = "This book is already checkout by someone.")

@app.route("/btn_pay<card_id>", methods=["GET"])
def btn_payfine(card_id):
	success = pay_fine(card_id)
	if(success):
		return render_template("message.html", msg = "success pay")
	else:
		return render_template("message.html", msg = "You can pay only after checkin that book.")

@app.route("/btn_checkin<Isbn>", methods=["GET"])
def btn_checkin(Isbn):
	date_in = datetime.now().strftime('%Y-%m-%d')
	db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
	cursor = db.cursor()
	cursor.execute('USE Library;')
	updatesql = '''UPDATE BOOK_LOANS SET Date_in = %s WHERE Isbn = %s ;'''
	cursor.execute(updatesql,([date_in, Isbn]))
	db.commit()
	cursor.close()
	db.close()
	return render_template("message.html", msg = "Checked in success")

@app.route("/add_borrower", methods=["POST"])
def add_borrower():
	form = request.form
	bname = form.get('Bname')
	ssn = form.get('Ssn')
	address = form.get('Address')
	phone = form.get('Phone')
	if(ssn and bname):
		db = mc.connect(host='localhost', user='root', passwd='Mysqlpassword',charset='utf8')
		cursor = db.cursor()
		cursor.execute('USE Library;')
		insert_sql = 'INSERT INTO BORROWER (Ssn,Bname,Address,Phone)VALUES(%s,%s,%s,%s);'
		cursor.execute(insert_sql,[ssn,bname,address,phone])
		db.commit()
		cursor.close()
		db.close()
		return render_template("message.html", msg = "Add borrower success")
	else:
		return render_template("message.html", msg = "You must fill ssn and name")


# navbar route
@app.route("/")
def ini_page():
	return render_template("main.html")
@app.route("/main_page")
def main_page():
	return render_template("main.html")
@app.route("/search_page")
def search_page():
	return render_template("search.html")
@app.route("/checkin_page")
def checkin_page():
	return render_template("checkin.html")
@app.route("/borrower_page")
def borrower_page():
	return render_template("bm.html")
@app.route("/fines_page")
def fine_page():
	result = fine_list()
	return render_template("fines.html", result = result)

if(__name__ == "__main__"):
	app.run(host = '127.0.0.1', debug= True, threaded = True)