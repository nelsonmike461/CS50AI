import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    # Initialize probability distribution
    distribution = {}
    num_pages = len(corpus)

    # Calculate random probability for each page (probability of randomly jumping to any page)
    random_prob = (1 - damping_factor) / num_pages

    # Initialize each page with the random probability
    for p in corpus:
        distribution[p] = random_prob

    # If current page has no outgoin links, treat it as having links to all pages
    if not corpus[page]:
        for p in corpus:
            distribution[p] += damping_factor / num_pages
    else:
        # Add additional probability for the pages that are linked to from current page
        num_links = len(corpus[page])
        for linked_page in corpus[page]:
            distribution[linked_page] += damping_factor / num_links

    return distribution


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    # Initialize PageRank counts for each page
    page_counts = {page: 0 for page in corpus}

    # Choose first sample randomly from all pages
    current_page = random.choice(list(corpus.keys()))
    page_counts[current_page] += 1

    # Generate remaining n-1 samples
    for _ in range(n-1):
        # Get probability distribution for next page  
        probabilities = transition_model(corpus, current_page, damping_factor)

        # Choose next page based on probability distribution
        pages = list(probabilities.keys())
        weights = [probabilities[page] for page in pages]
        current_page = random.choices(pages, weights=weights)[0]

        # Update count for selected page
        page_counts[current_page] += 1
    
    # Convert counts to probabilities
    return {page: count / n for page, count in page_counts.items()}


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    N = len(corpus)  # Total number of pages
    page_rank = {page: 1 / N for page in corpus}  # Initialize PageRank

    while True:
        old_page_rank = page_rank.copy()  # Store old PageRank values

        for page in corpus:
            rank_sum = 0
            for linking_page in corpus:
                # If linking_page has no outgoing links, treat it as linking to all pages
                if not corpus[linking_page]:
                    rank_sum += old_page_rank[linking_page] / N
                elif page in corpus[linking_page]:
                    num_links = len(corpus[linking_page])
                    rank_sum += old_page_rank[linking_page] / num_links

            # Apply PageRank formula
            page_rank[page] = (1 - damping_factor) / N + damping_factor * rank_sum

        # Check for convergence (no value changes by more than 0.001)
        if all(abs(page_rank[page] - old_page_rank[page]) < 0.001 for page in page_rank):
            break

    return page_rank


if __name__ == "__main__": 
    main()