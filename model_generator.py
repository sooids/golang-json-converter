import json2go
import json
import argparse
import fnmatch
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Golang Json Model Generator')
    parser.add_argument('--input', type=str, help='Original Json Path')
    parser.add_argument('--output', type=str, help='Model Output Path')
    parser.add_argument('--package', type=str, help='Package Name')
    parser.add_argument('--caution', action='store_true')

    args = parser.parse_args()
    if not args.input or not args.output:
        parser.print_help()
        exit(-1)

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    inputs = list()

    listOfFiles = os.listdir(args.input)  
    pattern = "*.json"  
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
            inputs.append(os.path.join(args.input, entry))

    for path in inputs:
        with open(path) as f:
            conv = json2go.JsonToGo()
            save_path = os.path.normpath(os.path.join(os.path.abspath(args.output), os.path.splitext(os.path.basename(path))[0] + ".go"))
            with open(save_path, "w") as w:
                if args.caution:
                    w.write("// Code generated by go generate; DO NOT EDIT\n\n")
                if args.package:
                    w.write("package %s\n\n"%(args.package))
                w.write(conv.Convert(f.read(), os.path.splitext(os.path.basename(path))[0]))
                print(save_path, "- Saved")
    
    print("Done.")
