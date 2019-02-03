import os
from flask import Flask, render_template, flash, redirect
from flask_script import Shell, Manager
from flask_wtf import Form
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'secret default value')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)

def make_shell_context():
    return {
        'app': app,
        'db': db,
        'Category': Category,
        'Product': Product
    }

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    products = db.relationship('Product', backref='category')

    def __repr__(self):
        return 'Category: %r' % self.name

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    def __repr__(self):
        return 'Product: %r' % self.name

class NewProductForm(Form):
    def __init__(self, *args, **kwargs):
        super(NewProductForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cat.id, cat.name) for cat in Category.query.all()]

    name = StringField('Product', validators=[DataRequired()])
    category = SelectField('Category', coerce=int)
    submit = SubmitField('Save')

@app.route('/', methods=['GET'])
def index():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route('/new', methods=['GET', 'POST'])
def new_product():
    name, category = None, None
    form = NewProductForm()
    if form.validate_on_submit():
        name = form.name.data
        category = form.category.data
        if Product.query.filter_by(name=name).first() is None:
            product = Product(name=name)
            product.category = Category.query.get_or_404(category)
            db.session.add(product)
            db.session.commit()
            flash("Product# {} has been created.".format(product.id))
            return redirect('/')

        else:
            flash("A product with name: '{}' already exists.".format(name))

        form.name.data = ""
        form.category.data = ""
    return render_template('new.html', form=form, name=name)

@app.route('/<int:id>/', methods=['GET'])
def view_product(id):
    product = Product.query.get_or_404(id)
    return render_template('view.html', product=product)

@app.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_product(id):
    form = NewProductForm()
    if form.validate_on_submit():
        other_product = Product.query.filter_by(name=form.name.data).first()
        if other_product is None or id == other_product.id:
            product = Product.query.get_or_404(id)
            product.name = form.name.data
            product.category = Category.query.get_or_404(form.category.data)
            db.session.add(product)
            db.session.commit()
            flash("Product# {} has been updated.".format(product.id))
            return redirect('/')

        else:
            flash("A product with name: '{}' already exists.".format(form.name.data))

    product = Product.query.get_or_404(id)
    form.name.data = product.name
    form.category.data = product.category.id    
    return render_template('edit.html', form=form)

@app.route('/<int:id>/delete', methods=['GET'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    flash('Product# {} has been deleted.'.format(id))
    return redirect('/')

manager.add_command("shell", Shell(make_shell_context))
if __name__ == '__main__':
    manager.run()