from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os, uuid
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-before-production")
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED = {"jpg","jpeg","png","webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "nextlove"),
    )

def allowed_file(name):
    return "." in name and name.rsplit(".",1)[1].lower() in ALLOWED

@app.route("/")
def index():
    c=db(); cur=c.cursor(cursor_factory=RealDictCursor)
    cur.execute("""SELECT p.*,u.name seller FROM products p JOIN users u ON p.seller_id=u.id
                   WHERE p.status='available' AND p.quantity > 0 ORDER BY p.created_at DESC""")
    products=cur.fetchall(); cur.close(); c.close()
    return render_template("index.html", products=products)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        c=db(); cur=c.cursor()
        try:
            cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                        (request.form["name"],request.form["email"],request.form["password"]))
            c.commit(); flash("สมัครสมาชิกสำเร็จ","success"); return redirect(url_for("login"))
        except psycopg2.Error:
            flash("อีเมลนี้ถูกใช้แล้ว","danger")
        finally: cur.close(); c.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db(); cur=c.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (request.form["email"],request.form["password"]))
        u=cur.fetchone(); cur.close(); c.close()
        if u:
            session["user_id"]=u["id"]; session["user_name"]=u["name"]; return redirect(url_for("index"))
        flash("อีเมลหรือรหัสผ่านไม่ถูกต้อง","danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/sell", methods=["GET","POST"])
def sell():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method=="POST":
        f=request.files.get("image"); filename=None
        if f and f.filename:
            if not allowed_file(f.filename):
                flash("รองรับ JPG, JPEG, PNG, WEBP เท่านั้น","danger"); return redirect(url_for("sell"))
            ext=f.filename.rsplit(".",1)[1].lower()
            filename=uuid.uuid4().hex+"."+ext
            f.save(os.path.join(UPLOAD_FOLDER,filename))
        c=db(); cur=c.cursor()
        cur.execute("""INSERT INTO products(seller_id,name,category,description,size,condition_text,price,image,quantity)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (session["user_id"],request.form["name"],request.form["category"],
                     request.form["description"],request.form["size"],request.form["condition_text"],
                     request.form["price"],filename,max(1,int(request.form.get("quantity",1)))))
        c.commit(); cur.close(); c.close()
        flash("ลงขายสินค้าเรียบร้อย","success"); return redirect(url_for("index"))
    return render_template("sell.html")

@app.route("/product/<int:pid>")
def product(pid):
    c=db(); cur=c.cursor(dictionary=True)
    cur.execute("""SELECT p.*,u.name seller FROM products p JOIN users u ON p.seller_id=u.id WHERE p.id=%s""",(pid,))
    p=cur.fetchone(); cur.close(); c.close()
    if not p: return "ไม่พบสินค้า",404
    return render_template("product.html", product=p)

@app.route("/cart")
def cart():
    if "user_id" not in session: return redirect(url_for("login"))
    raw=session.get("cart", {})
    cart_data={int(k): max(1,int(v)) for k,v in raw.items()}
    if not cart_data:
        return render_template("cart.html", items=[], grand_total=0, cart_count=0)
    c=db(); cur=c.cursor(dictionary=True)
    ids=list(cart_data.keys())
    placeholders=",".join(["%s"]*len(ids))
    cur.execute(f"SELECT p.*,u.name seller FROM products p JOIN users u ON p.seller_id=u.id WHERE p.id IN ({placeholders}) AND p.status='available'", ids)
    products=cur.fetchall(); cur.close(); c.close()
    valid={p["id"]:p for p in products if p["seller_id"] != session["user_id"] and p["quantity"] > 0}
    changed=False; items=[]; grand=0; count=0
    for pid, qty in cart_data.items():
        if pid not in valid:
            changed=True; continue
        p=valid[pid]
        new_qty=min(qty, int(p["quantity"]))
        if new_qty != qty: changed=True
        subtotal=float(p["price"])*new_qty
        items.append({"product":p,"quantity":new_qty,"subtotal":subtotal})
        grand += subtotal; count += new_qty
        cart_data[pid]=new_qty
    if changed: session["cart"]={str(k):v for k,v in cart_data.items()}
    return render_template("cart.html", items=items, grand_total=grand, cart_count=count)

@app.route("/cart/add/<int:pid>", methods=["POST","GET"])
def cart_add(pid):
    if "user_id" not in session: return redirect(url_for("login"))
    c=db(); cur=c.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE id=%s AND status='available'", (pid,))
    p=cur.fetchone(); cur.close(); c.close()
    if not p: flash("สินค้านี้ไม่มีแล้ว","danger"); return redirect(url_for("index"))
    if p["seller_id"] == session["user_id"]: flash("ไม่สามารถเพิ่มสินค้าของตัวเองลงตะกร้าได้","danger"); return redirect(url_for("product",pid=pid))
    cart=session.get("cart", {})
    key=str(pid); current=int(cart.get(key,0)); new=min(current+1, int(p["quantity"]))
    cart[key]=new; session["cart"]=cart
    flash("เพิ่มสินค้าลงตะกร้าแล้ว 🛒","success")
    return redirect(url_for("cart"))

@app.route("/cart/update/<int:pid>", methods=["POST"])
def cart_update(pid):
    if "user_id" not in session: return redirect(url_for("login"))
    qty=max(0,int(request.form.get("quantity",1)))
    cart=session.get("cart", {})
    key=str(pid)
    if qty==0: cart.pop(key,None)
    else:
        c=db(); cur=c.cursor(dictionary=True); cur.execute("SELECT quantity,status FROM products WHERE id=%s",(pid,)); p=cur.fetchone(); cur.close(); c.close()
        if not p or p["status"] != "available": cart.pop(key,None)
        else: cart[key]=min(qty,int(p["quantity"]))
    session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:pid>", methods=["POST","GET"])
def cart_remove(pid):
    if "user_id" not in session: return redirect(url_for("login"))
    cart=session.get("cart", {}); cart.pop(str(pid),None); session["cart"]=cart
    return redirect(url_for("cart"))

@app.route("/cart/clear", methods=["POST","GET"])
def cart_clear():
    if "user_id" not in session: return redirect(url_for("login"))
    session["cart"]={}; return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET","POST"])
def checkout_cart():
    if "user_id" not in session: return redirect(url_for("login"))
    raw=session.get("cart", {})
    cart_data={int(k): max(1,int(v)) for k,v in raw.items()}
    if not cart_data:
        flash("ตะกร้าสินค้าว่าง","danger"); return redirect(url_for("cart"))
    c=db(); cur=c.cursor(dictionary=True)
    ids=list(cart_data.keys()); placeholders=",".join(["%s"]*len(ids))
    cur.execute(f"SELECT * FROM products WHERE id IN ({placeholders}) AND status='available'", ids)
    products=cur.fetchall(); cur.close()
    by_id={p["id"]:p for p in products}
    items=[]; grand=0
    for pid,qty in cart_data.items():
        p=by_id.get(pid)
        if not p or p["seller_id"] == session["user_id"] or int(p["quantity"]) < qty:
            c.close(); flash("มีสินค้าในตะกร้าที่จำนวนไม่เพียงพอหรือไม่พร้อมขาย","danger"); return redirect(url_for("cart"))
        subtotal=float(p["price"])*qty; grand += subtotal
        items.append((p,qty,subtotal))
    if request.method=="POST":
        payment=request.form["payment"]; shipping=request.form["shipping"]
        try:
            cur2=c.cursor()
            for p,qty,subtotal in items:
                cur2.execute("INSERT INTO orders(buyer_id,seller_id,product_id,quantity,total,payment_method,shipping_method) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (session["user_id"],p["seller_id"],p["id"],qty,subtotal,payment,shipping))
                cur2.execute("UPDATE products SET quantity=quantity-%s, status=CASE WHEN quantity-%s<=0 THEN 'sold' ELSE 'available' END WHERE id=%s AND quantity>=%s AND status='available'", (qty,qty,p["id"],qty))
                if cur2.rowcount != 1: raise ValueError("สินค้าเปลี่ยนสถานะระหว่างสั่งซื้อ")
            c.commit(); cur2.close(); c.close(); session["cart"]={}
            flash("สร้างคำสั่งซื้อจากตะกร้าเรียบร้อยแล้ว 🛒","success"); return redirect(url_for("orders"))
        except Exception:
            c.rollback(); c.close(); flash("ไม่สามารถสร้างคำสั่งซื้อได้ กรุณาลองใหม่","danger"); return redirect(url_for("cart"))
    c.close()
    return render_template("checkout.html", items=[{"product":p,"quantity":q,"subtotal":st} for p,q,st in items], grand_total=grand)

@app.route("/checkout/<int:pid>", methods=["GET","POST"])
def checkout_legacy(pid):
    if "user_id" not in session: return redirect(url_for("login"))
    session["cart"]={str(pid):1}
    return redirect(url_for("checkout_cart"))

@app.route("/orders")
def orders():
    if "user_id" not in session: return redirect(url_for("login"))
    c=db(); cur=c.cursor(dictionary=True)
    cur.execute("""SELECT o.*,p.name product_name,p.image FROM orders o JOIN products p ON o.product_id=p.id
                   WHERE o.buyer_id=%s OR o.seller_id=%s ORDER BY o.created_at DESC""",
                (session["user_id"],session["user_id"]))
    rows=cur.fetchall(); cur.close(); c.close()
    return render_template("orders.html",orders=rows)

@app.route("/complaint",methods=["GET","POST"])
def complaint():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method=="POST":
        f=request.files.get("evidence"); filename=None
        if f and f.filename and allowed_file(f.filename):
            filename="complaint_"+uuid.uuid4().hex+"."+f.filename.rsplit(".",1)[1].lower()
            f.save(os.path.join(UPLOAD_FOLDER,filename))
        c=db(); cur=c.cursor()
        cur.execute("""INSERT INTO complaints(user_id,type,detail,evidence)
                       VALUES(%s,%s,%s,%s)""",
                    (session["user_id"],request.form["type"],request.form["detail"],filename))
        c.commit(); cur.close(); c.close()
        flash("ส่งเรื่องร้องเรียนแล้ว","success"); return redirect(url_for("index"))
    return render_template("complaint.html")

@app.route("/profile")
def profile():
    if "user_id" not in session: return redirect(url_for("login"))
    c=db(); cur=c.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE seller_id=%s ORDER BY created_at DESC",(session["user_id"],))
    products=cur.fetchall()
    cur.execute("""SELECT COALESCE(SUM(total),0) gross,COALESCE(SUM(total*0.15),0) fee,
                   COALESCE(SUM(total*0.85),0) net FROM orders
                   WHERE seller_id=%s AND status IN ('paid','shipped','received')""",(session["user_id"],))
    sales=cur.fetchone(); cur.close(); c.close()
    return render_template("profile.html",products=products,sales=sales)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
