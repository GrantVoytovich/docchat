"""Generate a self-contained sample PDF to test retrieval (no external download)."""
from fpdf import FPDF

SECTIONS = [
    ("Orchard Valley Co-op — Member Handbook",
     "Orchard Valley Co-op is a member-owned grocery founded in 1979 in Burlington. "
     "The co-op is governed by an elected nine-member board and operates on a one-"
     "member-one-vote basis. Any resident may join by purchasing a single equity "
     "share for $200, refundable when membership ends."),
    ("Member benefits",
     "Members receive a standing 8% discount on bulk goods and a 2% patronage dividend "
     "on annual purchases when the co-op posts a surplus. Members working four volunteer "
     "hours per month earn an additional 5% working-member discount. Dividends are paid "
     "each February for the prior fiscal year, which runs July 1 through June 30."),
    ("Shopping and returns",
     "The store is open 7am to 9pm daily. Perishable items may be returned within three "
     "days with a receipt; non-perishables within thirty days. Special orders require a "
     "25% deposit and cannot be refunded once placed with the supplier."),
    ("Governance and voting",
     "The annual meeting is held the first Saturday of October. A quorum is 10% of active "
     "members. Board elections use ranked-choice voting. Bylaws may be amended by a two-"
     "thirds vote of members present at any meeting where the amendment was noticed at "
     "least fourteen days in advance."),
    ("Volunteer program",
     "Working members sign up for shifts through the online portal. Common roles include "
     "shelf stocking, cashiering, and the Saturday farm pickup. Missing two consecutive "
     "committed shifts without notice pauses the working-member discount until a make-up "
     "shift is completed."),
    ("Sustainability commitments",
     "The co-op sources at least 40% of produce from farms within 100 miles and has "
     "committed to carbon-neutral operations by 2030. Single-use plastic bags were "
     "eliminated in 2021; members are encouraged to bring reusable containers for the "
     "bulk aisle, which are tared at the register."),
]

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=18)
for i, (title, body) in enumerate(SECTIONS):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16 if i == 0 else 14)
    pdf.multi_cell(0, 9, title)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 7, body)
pdf.output("data/sample_handbook.pdf")
print("wrote data/sample_handbook.pdf")
