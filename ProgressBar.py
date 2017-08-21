import progressbar

def AddLine(StatusLine):
    """
	Add a line containing STATUS to be added to the progress bar.
    """
    current_no_of_completed_tests, total_no_of_tests = StatusLine.split(' <|> ')[2].split('/')
    pbar = progressbar.ProgressBar(maxval = int(total_no_of_tests)).start()
    pbar.update(int(current_no_of_completed_tests))