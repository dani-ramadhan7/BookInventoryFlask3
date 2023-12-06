from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from io import BytesIO
import base64
import pytz  # Add this import statement

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Mendefinisikan model Buku dan LogPersediaan
class Buku(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    penulis = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    stok = db.Column(db.Integer, nullable=False)
    gambar = db.Column(db.String(255), nullable=False)
    log_persediaan = db.relationship('LogPersediaan', backref='buku', lazy=True, cascade="all, delete-orphan")

class LogPersediaan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    perubahan_kuantitas = db.Column(db.Integer, nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    
    # Mengubah default ke fungsi yang mengembalikan waktu saat ini di zona waktu Jakarta
    def default_timestamp(context):
        jakarta_timezone = pytz.timezone('Asia/Jakarta')
        return datetime.now(jakarta_timezone)

    timestamp = db.Column(db.DateTime, default=default_timestamp)

    id_buku = db.Column(db.Integer, db.ForeignKey('buku.id'), nullable=False)

def dapatkan_tingkat_persediaan():
    tingkat_persediaan = {}
    for buku in buku_buku:
        tingkat_persediaan[buku['nama']] = buku['stok']
    return tingkat_persediaan

@app.route('/')
def beranda():
    buku_buku = Buku.query.all()
    return render_template('index_bootstrap.html', buku_buku=buku_buku)

@app.route('/buku/<int:id_buku>')
def detail_buku(id_buku):
    buku = Buku.query.get(id_buku)
    if buku:
        return render_template('detail_buku.html', buku=buku)
    return 'Buku tidak ditemukan', 404

# SQLite
@app.route('/buku/<int:id_buku>/edit_persediaan', methods=['GET', 'POST'])
def edit_persediaan(id_buku):
    buku = Buku.query.get(id_buku)
    if request.method == 'POST':
        perubahan_kuantitas = int(request.form['kuantitas'])
        deskripsi = request.form['deskripsi']
        
        # Atur zona waktu ke Jakarta (GMT+7)
        jakarta_timezone = pytz.timezone('Asia/Jakarta')
        timestamp = datetime.now(jakarta_timezone)

        # Memperbarui catatan database
        buku.stok += perubahan_kuantitas
        db.session.add(LogPersediaan(perubahan_kuantitas=perubahan_kuantitas, deskripsi=deskripsi, timestamp=timestamp, buku=buku))
        db.session.commit()

        return redirect(url_for('detail_buku', id_buku=id_buku))
    return render_template('edit_persediaan.html', buku=buku)

@app.route('/log_persediaan')
def log_persediaan():
    semua_log = []
    for buku in buku_buku:
        for log in buku['log_persediaan']:
            semua_log.append({'nama_buku': buku['nama'], 'perubahan_kuantitas': log['perubahan_kuantitas'], 'deskripsi': log['deskripsi'], 'timestamp': log['timestamp']})
    semua_log.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('log_persediaan.html', logs=semua_log)

# SQLite
@app.route('/tambah_buku', methods=['GET', 'POST'])
def tambah_buku():
    if request.method == 'POST':
        buku_baru = Buku(
            nama=request.form['nama'],
            penulis=request.form['penulis'],
            deskripsi=request.form['deskripsi'],
            stok=int(request.form['stok']),
            gambar=request.form['gambar']
        )
        db.session.add(buku_baru)
        db.session.commit()
        return redirect(url_for('beranda'))
    return render_template('tambah_buku.html')

@app.route('/edit_buku/<int:id_buku>', methods=['GET', 'POST'])
def edit_buku(id_buku):
    buku = Buku.query.get(id_buku)
    if request.method == 'POST':
        buku.nama = request.form['nama']
        buku.penulis = request.form['penulis']
        buku.deskripsi = request.form['deskripsi']
        buku.stok = int(request.form['stok'])
        buku.gambar = request.form['gambar']
        db.session.commit()
        return redirect(url_for('detail_buku', id_buku=id_buku))
    return render_template('edit_buku.html', buku=buku)

@app.route('/hapus_buku/<int:id_buku>')
def hapus_buku(id_buku):
    buku = Buku.query.get(id_buku)
    if buku:
        # Menghapus log terkait
        LogPersediaan.query.filter_by(id_buku=buku.id).delete()

        db.session.delete(buku)
        db.session.commit()
    return redirect(url_for('beranda'))

if __name__ == '__main__':
    app.run(debug=True)