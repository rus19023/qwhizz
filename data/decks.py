# data/decks.py

DECKS = {
    "Week 1 – Chromosomes": [
        {"question": "What is a chromosome?", 
         "answer": "A DNA molecule packaged with proteins that carries genetic information"},

        {"question": "What are sister chromatids?", 
         "answer": "Identical copies of a chromosome joined at the centromere"},

        {"question": "What is a centromere?", 
         "answer": "The region where sister chromatids are held together"},

        {"question": "Difference between homologous chromosomes and sister chromatids?", 
         "answer": "Homologous chromosomes come from different parents; sister chromatids are identical copies"}
    ],

    "Week 2 – Meiosis & DNA Structure": [
        {"question": "Purpose of meiosis?", 
         "answer": "To produce haploid gametes and increase genetic diversity"},

        {"question": "What happens during Prophase I?", 
         "answer": "Homologous chromosomes pair and crossing over occurs"},

        {"question": "What is crossing over?", 
         "answer": "Exchange of genetic material between homologous chromosomes"},

        {"question": "Basic structure of DNA?", 
         "answer": "Double helix made of nucleotides with sugar, phosphate, and nitrogenous base"},

        {"question": "Base pairing rules?", 
         "answer": "A pairs with T, C pairs with G"}
    ],

    "Week 3 – DNA Replication": [
        {"question": "When does DNA replication occur?", 
         "answer": "During S phase of the cell cycle"},

        {"question": "Role of DNA helicase?", 
         "answer": "Unwinds the DNA double helix"},

        {"question": "Role of DNA polymerase?", 
         "answer": "Adds complementary nucleotides to synthesize new DNA"},

        {"question": "Leading vs lagging strand?", 
         "answer": "Leading strand is continuous; lagging strand is synthesized in Okazaki fragments"},

        {"question": "Why is DNA replication semi-conservative?", 
         "answer": "Each new DNA molecule contains one original strand and one new strand"}
    ]
}

# # Exam 1 Flashcards — MongoDB Ready (Exact 27 Questions)

# ```json
# {
#   "_id": "Exam 1 – Biology Review (Exact Questions)",
#   "cards": [
#     {"question": "What does the BYU–Idaho Honor Code require regarding academic honesty?", "answer": "Students must act honestly and ethically, avoiding cheating, plagiarism, or any form of academic dishonesty."},
#     {"question": "What behaviors constitute a violation of the BYU–Idaho Honor Code during exams?", "answer": "Cheating, using unauthorized materials, sharing answers, or receiving unauthorized assistance."}, 

#     {"question": "What is a hypothesis?", "answer": "A testable explanation for an observation or scientific question."},
#     {"question": "What distinguishes a scientific theory from a scientific law?", "answer": "A theory explains why phenomena occur; a law describes what happens."},
#     {"question": "What is the correct order of the steps of the scientific method?", "answer": "Observation, question, hypothesis, experiment, data analysis, conclusion."},
#     {"question": "What is the difference between an independent variable and a dependent variable?", "answer": "The independent variable is manipulated; the dependent variable is measured."},
#     {"question": "Why are controlled experiments important in science?", "answer": "They allow scientists to isolate variables and determine cause-and-effect relationships."},

#     {"question": "What are the three main subatomic particles of an atom?", "answer": "Protons, neutrons, and electrons."},
#     {"question": "Which subatomic particle determines how atoms interact chemically?", "answer": "Electrons."},
#     {"question": "What is the difference between ionic bonds and covalent bonds?", "answer": "Ionic bonds involve electron transfer; covalent bonds involve sharing electrons."},
#     {"question": "Why is water such an effective solvent for biological molecules?", "answer": "Because water is polar and can form hydrogen bonds with other polar substances."},

#     {"question": "What are the four major classes of biological macromolecules?", "answer": "Carbohydrates, lipids, proteins, and nucleic acids."},
#     {"question": "What is the primary function of carbohydrates in cells?", "answer": "To provide energy and structural support."},
#     {"question": "What roles do lipids play in living organisms?", "answer": "They form cell membranes and provide long-term energy storage."},
#     {"question": "What is the primary role of proteins in cells?", "answer": "They act as enzymes and perform most cellular functions."},
#     {"question": "Which biomolecule stores genetic information?", "answer": "Nucleic acids, specifically DNA and RNA."},

#     {"question": "What are the three main statements of cell theory?", "answer": "All living things are made of cells; cells are the basic unit of life; all cells come from preexisting cells."},
#     {"question": "What is the difference between prokaryotic and eukaryotic cells?", "answer": "Eukaryotic cells have a nucleus; prokaryotic cells do not."},
#     {"question": "What is the function of the nucleus?", "answer": "To store DNA and control cellular activities."},
#     {"question": "What is the function of mitochondria?", "answer": "To produce ATP through cellular respiration."},
#     {"question": "What is the role of ribosomes?", "answer": "To synthesize proteins."},

#     {"question": "What are the components of a DNA nucleotide?", "answer": "A sugar, a phosphate group, and a nitrogenous base."},
#     {"question": "What are the base-pairing rules in DNA?", "answer": "Adenine pairs with thymine; cytosine pairs with guanine."},
#     {"question": "What is a chromosome?", "answer": "A DNA molecule packaged with proteins that carries genetic information."},
#     {"question": "What are sister chromatids?", "answer": "Identical copies of a chromosome joined at the centromere."},
#     {"question": "What is the purpose of mitosis?", "answer": "To produce identical cells for growth and repair."},
#     {"question": "What is the purpose of meiosis?", "answer": "To produce haploid gametes and increase genetic diversity."}
#   ]
# }
# ```

# ---

# ### How to Use This

# * Import directly into MongoDB (`decks` collection)
# * One card = one exam question
# * Covers **exactly the 27 questions** from the review

# You now have a complete, exam-accurate flashcard deck.

