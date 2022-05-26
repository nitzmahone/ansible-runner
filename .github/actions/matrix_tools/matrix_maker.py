import argparse
import json
import sys
import yaml


def main():
    parser = argparse.ArgumentParser(description='GHA dynamic matrix tools')

    subparsers = parser.add_subparsers(metavar='mode', required=True)
    yaml_to_matrix_parser = subparsers.add_parser('yaml-to-matrix', description='convert a yaml matrix from stdin to JSON')
    yaml_to_matrix_parser.add_argument('--output-var', required=True, help='set the output matrix JSON')
    yaml_to_matrix_parser.set_defaults(mode='')

    args = parser.parse_args()

    matrix = yaml.safe_load(sys.stdin)
    matrix_json = json.dumps(matrix)

    print(f'::set-output name={args.output_var}::{matrix_json}')


if __name__ == '__main__':
    main()