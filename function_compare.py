"""
Remove text comparison code from here.
"""

import os
import argparse

list_functions= {}
def get_functions(ida_input_dir, filename):
    """
    Read strings from files generated by an IDAPython script and store them in a list for further processing.
    """
    with open(ida_input_dir+'/'+filename,'rU') as f:
        t1= ''
        t2= ''
        t1= [line for line in f.readlines()]
        for function in t1:
            t2= function.split('$$$')
            list_functions[filename+'---'+t2[0]]= t2[1][:-1]

    return list_functions

def get_exe_to_reverse():
    """
    Read command line arguments.
    """
    parser= argparse.ArgumentParser()
    parser.add_argument('file', nargs=1, help='Enter the name of the file you want to reverse engineer here')
    parser.add_argument('-m', action="store_true", help='Use this if you want to compare only by mnemonics')
    args = parser.parse_args()

    return args.file[0], args.m

def function_compare(exe_to_reverse, list_functions):
    """
    Compare each function from the binary you want to reverse with all the functions from all other files
    """

    """
    Separate the functions of the binary and all the libraries so its easy to compare content.
    """
    libraries= {}
    match_count= 0

    for key in list_functions.keys():
        if not key.startswith(exe_to_reverse+'---'):
            libraries[key]= list_functions[key]
            del list_functions[key]

    """
    Compare the actual instructions and do the analysis of what matched.
    """
    non_matching_instructions= {}
    matched_functions= {}
    instructions1= ''
    instructions2= ''

    for key1, value1 in list_functions.items():
        key1= key1.split('---')[1]
        for key2, value2 in libraries.items():
            key2= key2.split('---')[1]
            instructions1= value1.split('^^^')
            instructions2= value2.split('^^^')
            match_count= 0
            func_match_flag= 0

            """
            Do the function names match? I'm not sure this is robust though - will the functions get loaded at the same offsets in the binary
            and the library as well if both are loaded independently? Anyway, it's a start :)
            """
            if key1 == key2: 
                func_match_flag= 1
                non_matching_instructions[key1]= ''
                for i1 in instructions1:
                    flag =0
                    i1= i1.rstrip()
                    for i2 in instructions2:
                        i2= i2.rstrip()
                        if i1 == i2:
                            match_count+=1
                            flag= 1
                            break
                        else:
                            continue

                    """
                    Track the instructions that do not match, per function.
                    """
                    if flag == 0:
                        non_matching_instructions[key1]+= i1
                        non_matching_instructions[key1]+= '\n'
            else:
                continue
        
        """    
        If there is an exact match, store the 2nd function's name as a value to print later, otherwise store the number of instructions that
        actually matched.
        """
        if match_count == len(instructions1) and func_match_flag== 1:
            matched_functions[key1]= key2
        elif match_count != len(instructions1) and func_match_flag== 1:
            matched_functions[key1]= key2+':'+str(len(instructions1) - match_count)
        elif func_match_flag == 0:
            matched_functions[key1]= 'na'
            
    return non_matching_instructions, matched_functions

def function_compare_by_mnem(exe_to_reverse, list_functions):
    """
    Compare each function from the binary you want to reverse with all the functions from all other files
    """

    """
    Separate the functions of the binary and all the libraries so its easy to compare content.
    """
    libraries= {}

    for key in list_functions.keys():
        if not key.startswith(exe_to_reverse+'---'):
            libraries[key]= list_functions[key]
            del list_functions[key]

    # Compare just the mnemonics of functions. The danger here is false positives. Lets see though.
    matched_functions= {}
    for key1, value1 in list_functions.items():
        key1= key1.split('---')[1]
        flag= 0
        for key2, value2 in libraries.items():
            key2= key2.split('---')[1]
            
            value1= value1.rstrip()
            value2= value2.rstrip()
            t1= value1.split('<')
            t2= value2.split('<')
            if t1[0] == t2[0]:
                flag= 1
                matched_functions[key1+'<'+t1[1]]= key2
                break
            else:
                continue

    return matched_functions

def write_results(output_file, matched_functions, non_matching_instructions):
    """
    Write results to a file that should then be loaded into IDA
    """
    with open(output_file,'a') as f:
        """
        Can write all changed instructions as well, for reference purposes. Commented for now.
    
        for key,val in non_matching_instructions.items():
            f.write(str(non_matching_instructions.items()))
            f.write("\n")
        """

        for key,val in matched_functions.items():
            #if val != 'na':
            f.write(key+"\t"+str(val))
            f.write("\n")

if __name__ == "__main__":
    # Identify which the actual binary is and check if you want to compare by mnemonics
    exe_to_reverse, compare_by_mnem= get_exe_to_reverse()

    ida_input_dir= 'input'
    t2={}
    list_functions= {}

    #Read all the function names and bodies returned after parsing the IDB files of the binary and all the libraries
    if not compare_by_mnem:
        for filename in os.listdir(ida_input_dir):
            if not filename.endswith('_mnem.txt'):
                t2= get_functions(ida_input_dir, filename)
                list_functions= dict(t2.items()+list_functions.items())
            else:
                continue

    elif compare_by_mnem:
        for filename in os.listdir(ida_input_dir):
            if filename.endswith('_mnem.txt'):
                t2= get_functions(ida_input_dir, filename)
                list_functions= dict(t2.items()+list_functions.items())
            else:
                continue

    # This is what does the actual comparison
    non_matching_instructions={}
    if not exe_to_reverse.endswith('_mnem.txt'):
        non_matching_instructions, matched_functions = function_compare(exe_to_reverse, list_functions)
    elif exe_to_reverse.endswith('_mnem.txt'):
        matched_functions = function_compare_by_mnem(exe_to_reverse, list_functions)

    # Write IDA results to file
    output_file= 'input_to_rename_function.txt'
    
    if non_matching_instructions:
        write_results(output_file, matched_functions, non_matching_instructions)
    else:
        write_results(output_file, matched_functions, 'NA')
