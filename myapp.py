"""
This module contains a Flask web application for generating consultation reports.
It provides a form for inputting patient and consultation details, and generates
a PDF report upon form submission.
"""

import datetime
import os
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, send_file, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, FileField, DateField
from wtforms.validators import DataRequired, Regexp, ValidationError
from flask_ckeditor import CKEditor, CKEditorField

from weasyprint import HTML

ckeditor = CKEditor()

app = Flask(__name__)
app.config["SECRET_KEY"] = "sp6iwo1aebldsu1"
app.config["UPLOAD_FOLDER"] = "uploads/"
ckeditor.init_app(app=app)


def validate_date_not_above_current(field):
    """Custom validator to check date is not in the future."""
    try:
        if field.data > datetime.datetime.today().date():
            raise ValidationError("Date of birth cannot be in the future.")
    except ValueError as exc:
        raise ValidationError("Invalid date format. Please use YYYY-MM-DD.") from exc


# Custom validator for numbers only
def validate_numbers_only(field):
    """Custom validator to check field contains only numbers."""
    if not field.data.isdigit():
        raise ValidationError("This field should contain numbers only.")


# Form class definition
class ConsultationForm(FlaskForm):
    """Form for inputting consultation details."""

    clinic_name = StringField("Clinic Name", validators=[DataRequired()])
    clinic_logo = FileField(
        "Clinic Logo",
        validators=[FileRequired(), FileAllowed(["jpg", "png"], "Images only!")],
    )
    physician_name = StringField(
        "Physician Name",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z\s]*$", message="Physician name must contain characters only."
            ),
        ],
    )
    patient_contact = StringField(
        "Patient Contact", validators=[DataRequired(), validate_numbers_only]
    )
    patient_first_name = StringField(
        "Patient First Name",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z\s]*$",
                message="Patient first name must contain characters only.",
            ),
        ],
    )
    patient_last_name = StringField(
        "Patient Last Name",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z\s]*$",
                message="Patient last name must contain characters only.",
            ),
        ],
    )
    patient_dob = DateField(
        "Patient DOB",
        format="%Y-%m-%d",
        validators=[DataRequired(), validate_date_not_above_current],
    )
    physician_contact = StringField(
        "Physician Contact", validators=[DataRequired(), validate_numbers_only]
    )

    chief_complaint = CKEditorField(
        "chief_complaint", validators=[DataRequired()]
    )  # <--
    consultation_note = CKEditorField(
        "consultation_note", validators=[DataRequired()]
    )  # <--


# Route for the form
@app.route("/", methods=["GET", "POST"])
def index():
    """Route for rendering the consultation form and handling form submission."""
    form = ConsultationForm()
    if form.validate_on_submit():

        return generate_pdf(form)
    return render_template("index.html", form=form)


@app.route("/uploads/<path:path>")
def send_report(path):
    """Route for sending uploaded reports."""
    return send_from_directory("uploads", path)


@app.route("/templates/<path:path>")
def get_template(path):
    """Route for sending template files."""
    return send_from_directory("templates", path)


def generate_pdf(form):
    """Generates a PDF report from the submitted form data."""
    client_ip = request.remote_addr

    filename = f"CR_{form.patient_last_name.data}_{form.patient_first_name.data}_{form.patient_dob.data}.pdf"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    clinic_logo_path = "uploads/" + form.clinic_logo.data.filename
    form.clinic_logo.data.save(dst=clinic_logo_path)
    full_logo_path = request.base_url + "/" + clinic_logo_path

    rendered_html = render_template(
        "report.html",
        form=form,
        clinic_logo=full_logo_path,
        timestamp=timestamp,
        ip=client_ip,
    )

    html = HTML(string=rendered_html)
    html.write_pdf(filepath)

    # Send the PDF file as a response
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
