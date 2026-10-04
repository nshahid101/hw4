# AI Prompts Log — HW 4 (Campus Customs)

This file logs the prompts used while working through Problems 1–13. Each section includes:
- Problem number & title
- At least one prompt (in my own words)
- A follow-up prompt if one was needed, with a sentence on what the first prompt was missing

## Problem 1 —

**Prompt:**

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 2 — Database Analysis

**Prompt:**
"Analyze the database. Tell me what fields are in data/campus_customs.db and what each is categorizing. Also start output/harness.md"

**Follow-up prompt (if needed):**
"I need to edit the info in output/harness.md. It should include each table and field and one brief line on why each field matters either for the Campus Customs shop or for the chatbot. Mention for catalogue it's the repository for products available from the shop for the customer, inventory is how much of that product stock is left which would be important to help understand sell-through and accurate inventory tracking"
*What was lacking:* The first pass only listed each field's name/type with a generic note — it didn't explain why each field actually matters to the shop or the chatbot, which is what made the log useful for the assignment.

---

## Problem 3 — Build Campus Customs Website

**Prompt:**
"I'll need to scaffold a react + vite + typescript front end. I'll need to have a nav bar at the top that link to the main pages (Home, Products, About Us, Log In and Create Account). For the Home page, mimic the style font from the homepage of https://yalebulldogblue.com/. The home page should have a snapshot of some of the products available in the catalogue. Also include a call to action that says 'Come Visit Us' and add the address 57 Broadway, New Haven Connecticut. If possible, pin this on a map too. On the About Page, add a short description about the client Campus Customs which should mention they customize apparel and accessories for campus merchandise. On products page, include what you think a typical product page for apparel would have — product images from the catalogue, name, price and a short product description. Each product should open a single item page (large image on one side, full product text on the other — description, price, sizes/stock). Clicking a card on the Products page should take the user there. I also want to add a chat interface on the bottom right of the site (floating chat panel) — a stub that will call my backend later should be enough for this for now. Start a small API to read the database in backend/main.py to serve products and images for now."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 4 — Create Account and Login

**Prompt:**
"I want to build a standard 'create account' login flow. To create account a user will need to input first name, last name, email, password and confirm password. To login a user will need their email and password. New accounts would go into the users table and passwords should be stored securely so there is no unauthorized access. The second seed db has a test user to use while building (email is test@campuscustoms.yale.edu and password is password). Confirm I am able to log in using that user. I'll also want to test creating a brand new account. Output/harness.md will then need to be updated with how the authorization works (what is stored for a user and how passwords are protected)."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 5 — Pydantic AI Agent Backend

**Prompt:**
"I want to build a pydanticAI agent behind FastAPI that will be plugged into my front-end chat widget. The API app should be put into backend/main.py to be run with Uvicorn later. The agent will have these 4 files: backend/prompts/prompts.md, backend/agent.py, backend/tools.py, backend/models.py. main.py will also need to expose a chat route so a message from the website returns an answer from the agent (and anything else additional that might be needed)"

**Follow-up prompt (if needed):**
*What was lacking:* My first message only named 2 of the 4 files (prompts.md and agent.py) — I had to ask which two I'd left out before any code could be written, and clarified tools.py and models.py in a follow-up.

---

## Problem 6 — Tools: Product Info and Stock

**Prompt:**
"create a tool for the agent to look up real info from campus_customs.db. This should include product description, price and accurate inventory tracking (it should know how many items are in stock by size when a user asks). The agent should only reference the db - nothing like prices or quantities should be invented. If something is out of stock it should say so. Prompts/prompt.md need to be expanded so the agent knows to call these tools for price and stock questions. Return types should be updated in models.py. Output/harness.md should then list each tool and explain which model fields were chosen for lookup results and why - write this in easy to understand verbiage that a non technical person can understand and let me know what is in there."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 7 — Chat Search That Updates the Page

**Prompt:**
"Hoping to add a site feature where is a user asks about a type of item (like 'what t-shirts do you have') the agent should search the catalogue and the website should then dynamically show those matching items as product cards (inc image, name, price, short product description). This is an API contract so the agent should return structure product matched and the front end then renders this on the website. Once built, verify the single-item page behavior from q3 still works - each product card should still open a detailed view (the large image with the full info) when clicked, including the ones that chat just put on the page. Once again, update prompts/prompt.md and output/harnss.md in plain non-technical English with a short description of how search results reach the page."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 8 — Customer Memory

**Prompt:**
"When a user is logged in, their chat history should be saved in the db in a table (title it 'user chat history') and reloaded when they return. The agent should know who the user chatting is (name, email) - this should be put into an agent tool the agent can call. Add enough page context so if a user asks 'do you have this in pink' or any other similar question on a product page (like do you have something below or above a certain price or in a different size) the agent should know which item the user is referencing. Code can be put into the agent context to accomplish this. Chat history only needs to be kept for a logged-in user, otherwise guests can stull chat. In output/harness.md document in plain non-technical english how a user chat history is stored, what customer fields the agent sees (customer and user are interchangeable in meaning here) and how page context is passed."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 9 — Usability Improvements

**Prompt:**
"I need to make 2 front end usability improvements to make the site look better and easier to use. Can you provide a list of 4 improvements and I'll choose 2?"

**Follow-up prompt (if needed):**
"Can you work on implementing choices 1 and 4? Log what the improvement is and why it helps a customer shopping experience (can just paste what it written above) in output/usability.md. Ensure each improvement actually shows up in the running app."
*What was lacking:* The first prompt only asked for a list of options to choose from — it didn't request implementation, so a follow-up was needed once the 2 choices were made to actually build them and document/verify them.

---

## Problem 10 — Style the Website

**Prompt:**
"Can you make several suggestions on site design for font, color, hierarchy, motion, product presentation and chat feel that would improve the site? Suggestions that would help a customer be more likely to buy something are particularly welcomed. Feel free to take inpo for suggestions from other retail related sites like https://www.theharvardshop.com/ or https://shop.rolltide.com/"

**Follow-up prompt (if needed):**
"Could you implement the first font change you mentioned (pairing the serif with a sans-serif), the second color suggestion (using the yale-blue variable more), the second suggestion under hierarchy titled 'shop by category', under product presentation implement the first and third suggestions ('real, honest, urgency badges' and 'you might also like') and finally the first suggestion under chat feel 'giving the assistant name/personality' - specifically rename it to 'Ask the Bulldog' as suggested"
*What was lacking:* The first prompt only asked for a list of design suggestions to review — a follow-up was needed to pick specific items from the list and ask for them to actually be built.

---

## Problem 11 — Site Testing (App Check)

**Prompt:**
"I want to test the live site and document it in output/app_check.html which should be a page I can double click open. I'll need to include clear screenshots and short captions for the following: 1. Chat checking the inventory level if an item (with the honest stock and price from the DB) 2. The dynamic search-result cards appearing after a category question 3. One of the usability features added from problem 9. The html needs to be easy to grade - there should be a heading for each check, screenshot, and 1-2 sentences on what the screenshot is proving. The screenshot image files should be in output/app_check_images and linked from app_check.html with relative paths."

**Follow-up prompt (if needed):**
*What was lacking:*

---

## Problem 12 — Audit Trail, Safety, Finish Harness

**Prompt:**
"I'll need to keep an append-only output/audit_trail.json of agent-loop activity (inc time, tool name, short args/result, stop reason). Do not wipe this between runs. I'll also need to add some safety rules for the agent and put them in prompts/prompt.md - can you make a few suggestions?"

**Follow-up prompt (if needed):**
"Those sounds great and please implement all of the above and write them into prompts/prompts.md. Once set, I need to finish output/harness.md so it's clear how the system works. Please include the following: model fields in models.py and why they were chosen, tools and abilities, the safety rules, specs (loop limits, result caps, models, how to run front + back). Make sure this is in plain, easy to read English and let me know what is in here once set"
*What was lacking:* The first prompt only asked for safety-rule suggestions to review, not implementation — a follow-up was needed to approve all of them and request the full harness.md write-up.

---

## Problem 13 —

**Prompt:**

**Follow-up prompt (if needed):**
*What was lacking:*
