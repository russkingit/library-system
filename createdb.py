import mysql.connector as mc

db = mc.connect(
	host = 'localhost',
	user = 'root',
	passwd = 'Mysqlpassword',
	charset = 'utf8')
cursor = db.cursor()

cursor.execute('DROP DATABASE IF EXISTS Library')
cursor.execute('CREATE DATABASE Library')
cursor.execute('USE Library')

# # Create new table
cursor.execute('DROP TABLE IF EXISTS BOOK')
cursor.execute('''CREATE TABLE BOOK(
	Isbn CHAR(10) NOT NULL,
	Title VARCHAR(255) NOT NULL,
	PRIMARY KEY(Isbn)
	)''')
cursor.execute('DROP TABLE IF EXISTS AUTHORS')
cursor.execute('''CREATE TABLE AUTHORS(
	Author_id INT(8) NOT NULL AUTO_INCREMENT,
	Name VARCHAR(255) NOT NULL,
	PRIMARY KEY(Author_id),
	UNIQUE (Name)
	)''')
cursor.execute('DROP TABLE IF EXISTS BOOK_AUTHORS')
cursor.execute('''CREATE TABLE BOOK_AUTHORS(
	Author_id INT(8),
	Isbn CHAR(10),
	PRIMARY KEY(Author_id, Isbn),
	CONSTRAINT fk_Book_AUTHORS_AUTHORS FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id),
	CONSTRAINT fk_Book_AUTHORS_BOOK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn)
	)''')
cursor.execute('DROP TABLE IF EXISTS BORROWER')
cursor.execute('''CREATE TABLE BORROWER(
	Card_id INT(8) NOT NULL AUTO_INCREMENT,
	Ssn CHAR(11) NOT NULL,
	Bname VARCHAR(50) NOT NULL,
	Address VARCHAR(70) DEFAULT NULL,
	Phone CHAR(15),
	PRIMARY KEY(Card_id),
	UNIQUE(Ssn)
	)''')
cursor.execute('DROP TABLE IF EXISTS BOOK_LOANS')
cursor.execute('''CREATE TABLE BOOK_LOANS(
	Loan_id INT(8) NOT NULL AUTO_INCREMENT,
	Isbn CHAR(10) NOT NULL,
	Card_id INT(8) NOT NULL,
	Date_out DATE NOT NULL,
	Due_date DATE NOT NULL,
	Date_in DATE DEFAULT NULL,
	PRIMARY KEY(Loan_id),
	CONSTRAINT fk_BOOK_LOANS_BOOK FOREIGN KEY (Isbn) REFERENCES BOOK(Isbn),
	CONSTRAINT fk_BOOK_LOANS_BORROWER FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id)
	)''')
cursor.execute('DROP TABLE IF EXISTS FINES')
cursor.execute('''CREATE TABLE FINES(
	Loan_id INT(8) NOT NULL,
	Fine_amt DECIMAL(10,2) DEFAULT NULL,
	Paid INT(2) DEFAULT 0,
	PRIMARY KEY (Loan_id),
	CONSTRAINT fk_FINES_Loan_id FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS (Loan_id)
	)''')

# Insert book.csv to database
books = []
with open('books.csv') as file:
	rows = file.readlines()
	for row in rows[1:]:
		books.append(row.split('\t'))
sql_book = '''INSERT INTO BOOK(Isbn, Title) VALUES (%s, %s)'''
sql_author = '''INSERT IGNORE INTO AUTHORS(Name) VALUES (%s)'''
sql_authorbook = '''INSERT IGNORE INTO BOOK_AUTHORS(Author_id, Isbn) VALUES (%s, %s)'''
for book in books:
	val_book =(book[0], book[2])
	authors = book[3].split(',')
	authors = list(set(authors))
	cursor.execute(sql_book, val_book)
	for author in authors:
		val_author = (author,)
		cursor.execute(sql_author, val_author)
		cursor.execute('''SELECT Author_id FROM AUTHORS WHERE Name =%s''', val_author)
		author_id = cursor.fetchone()
		# print('author_id: ', author_id, 'isbn: ', book[0]);
		val_authorbook = (author_id[0], book[0])
		cursor.execute(sql_authorbook, val_authorbook)

# Insert borrower.csv
borrowers = []
with open('borrowers.csv') as file:
	rows = file.readlines()
	for row in rows[1:]:
		borrowers.append(row.split(','))
	sql_borrower = '''INSERT INTO BORROWER(Card_id, Ssn, Bname, Address, Phone) VALUES (%s, %s, %s, %s, %s)'''
	for borrower in borrowers:
		card_id = borrower[0]
		ssn = borrower[1]
		name = borrower[2] +' '+borrower[3]
		address= borrower[5]+', '+borrower[6]+', '+borrower[7]
		phone = borrower[8]
		val_borrower = (card_id, ssn, name, address, phone)
		cursor.execute(sql_borrower, val_borrower)

db.commit()
print('Finished')

db.close()