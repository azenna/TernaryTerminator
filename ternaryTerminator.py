import os
import re
from black import format_str, FileMode

# im almost 100% sure there is a simpler or atleast built in way to do this but I'm lazy
def getIndentValue(s):
    wCount = 0

    for c in s:
        if c == " ":
            wCount += 1
        else:
            break

    return wCount


# im very cautiously going to say this is working now
def findConditionals(lines):

    isConditional = False
    conditionals = []
    conditionalsInd = []
    conditional = []
    conditionalInd = []
    parentIndent = 0
    conditionalCounter = 0

    # finds all conditional statements and there children and puts them in a list
    for i in range(0, len(lines)):

        line = lines[i]

        # get indent for conditional building
        indent = getIndentValue(line)

        # if there is an if statement on the current line
        if bool(re.search("^\s*if.*", line)) and not isConditional:

            if conditionalCounter > 0:
                conditionals.append(conditional)
                conditionalsInd.append(conditionalInd)
                conditional = []
                conditionalInd = []

            isConditional = True
            parentIndent = indent
            conditional.append(line)
            conditionalInd.append(i)

            continue

        # catching elifs and elses
        if isConditional and bool(re.search("(^\s*elif.*)|(^\s*else.*)", line)):

            conditional.append(line)
            conditionalInd.append(i)

        elif isConditional and bool(re.search("(^\s*else.*)", line)):

            conditional.append(line)
            conditionalInd.append(i)

        # catch child statements
        elif isConditional and indent > parentIndent:

            conditional.append(line)
            conditionalInd.append(i)
            try:
                if getIndentValue(lines[i + 1]) <= parentIndent and not bool(
                    re.search("(^\s*elif.*)|(^\s*else.*)", lines[i + 1])
                ):
                    isConditional = False
                    parentIndent = 0
                    conditionalCounter += 1
            except:
                pass

    conditionals.append(conditional)
    conditionalsInd.append(conditionalInd)
    return conditionals, conditionalsInd


# takes a simple list representing a conditional and turns it into a ternary statement
def ternaryifier(conditional):

    ternary = ""

    # regex list for matching if elif and else
    rL = [re.compile(f"^{token}.*") for token in ["if", "elif", "else"]]

    question = ""
    children = ""
    indentLevel = getIndentValue(conditional[0])
    isElifEnd = False
    onlyIf = True
    isFirstChild = True
    childIndent = 0

    # add indent to ternary

    for i in range(len(conditional)):

        cond = conditional[i]
        indent = getIndentValue(cond)

        isElif = bool(re.search(rL[1], cond))
        isElse = bool(re.search(rL[2], cond))
        isEither = isElse or isElif

        # on the first iteration where starting if statement is
        if i == 0:
            question = cond.strip()[2:-1].strip()

        if isEither:
            onlyIf = False
            # add to ternary, delete from question and children
            # format string
            ternary += f"exec('{children}') if {question} else "

            # reset values
            question = ""
            children = ""

        if isElif:
            question = cond.strip()[4:-1].strip()
            isElifEnd = True
        if isElse:
            isElifEnd = False

        if indent > indentLevel:

            # control indent level so executable
            if isFirstChild:
                childIndent = getIndentValue(cond)
                cond = cond[childIndent:]
                isFirstChild = False

            else:
                cond = cond[childIndent:]

            # fmt: off
            children += cond.replace("'", "\\'").replace('"', '\\"').replace("\n","\\n")
            # fmt: on

    # doesn't get to last conditional so we need to do last operation outside of loop.
    if isElifEnd or onlyIf:
        ternary += f"exec('{children}') if {question} else exec(None)"
    else:
        ternary += f"exec('{children}')"

    return ternary + "\n"


# main function to handle reading and writing
def ternaryMain():

    files = os.listdir()

    # list comp to weed out non python files and this file
    files = [
        file
        for file in files
        if file.endswith(".py") and file != "ternaryTerminator.py"
    ]

    # main loop for reading and writing to files
    for file in files:

        filename = file

        # code formatting for standardization
        file = open(filename, "r")
        blackString = file.read()
        file.close()

        blackFormat = format_str(blackString, mode=FileMode())
        file = open(filename, "w")
        file.write(blackFormat)
        file.close()

        # I really like file so Im gonna reuse it for everything
        file = open(filename, "r+")
        lines = file.readlines()
        file.close()

        # remove all extraneous lines for simplicity
        lines = [line for line in lines if not bool(re.search("^\s*\n", line))]

        # retrieve all conditionals from lines in nested list format
        conditionals, conditionalsInd = findConditionals(lines)

        # skip this file if there are no conditionals
        if not conditionals[0]:
            continue

        # loop to turn conditional in to ternary and write it to file
        for i in range(len(conditionals)):

            # values for loop
            cond = conditionals[i]
            condI = conditionalsInd[i]

            ternary = ternaryifier(cond)

            # where the ternary will be inserted
            newI = condI[0]

            # insert into lines
            lines[newI] = ternary

            # replace old linew with None
            condI = condI[1:]
            for i in condI:
                lines[i] = None

        # take out all lines that are none
        lines = [line for line in lines if line is not None]

        # write to the file
        file = open(filename, "w")
        file.write("".join(lines))


if __name__ == "__main__":
    ternaryMain()
