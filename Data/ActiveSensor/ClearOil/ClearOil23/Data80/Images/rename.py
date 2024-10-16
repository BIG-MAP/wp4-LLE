import os
# Function to rename multiple files
def main():
	i = 0
	path="."
	for i in range(169):
		source = "a"+str(i)+".jpg"
		destination ="funnel" + str(i) + ".jpg"
		if source in os.listdir(path):
			print(source)
			print(destination)
			os.rename(source, destination)
		#my_source =path + filename
		#my_dest =path + my_dest
		# rename() function will
		# rename all the files
		
	#	i += 1
# Driver Code
if __name__ == '__main__':
	# Calling main() function
	main()