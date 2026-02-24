import subprocess
from pathlib import Path


class PytestRunner:

    def __init__(self, project_root: Path, source_patterns: list[str]):
        self.project_root = project_root
        self.source_patterns = source_patterns

    def _extract_base_dirs(self) -> list[str]:
        # Izvlekaem bazovye direktorii iz patternov
        # src/**/*.py -> src
        # tests/**/*.py -> tests
        base_dirs = set()
        for pattern in self.source_patterns:
            # Beryom pervuyu chast' do /**
            if '/**' in pattern:
                base_dir = pattern.split('/**')[0]
            elif '**' in pattern:
                base_dir = pattern.split('**')[0].rstrip('/')
            else:
                # Prosto direktoriya
                base_dir = pattern
            
            if base_dir:
                base_dirs.add(base_dir)
        
        return list(base_dirs)

    def run_with_coverage_and_durations(self) -> bool:
        # Zapusk pytest s coverage i sborom vremeni vypolneniya
        
        # Izvlekaem bazovye direktorii dlya coverage
        base_dirs = self._extract_base_dirs()
        if not base_dirs:
            print("Warning: No base directories found in source patterns")
            return False
        
        # Formiruem komandu dlya pytest
        cmd = ["pytest"]
        
        # Dobavlyaem coverage dlya kazhdoy bazovoy direktorii
        for base_dir in base_dirs:
            cmd.append(f"--cov={base_dir}")
        
        cmd.extend([
            "--cov-context=test",
            "--cov-report=",  # Otklyuchaem generatsiyu otcheta
        ])

        print(f"Running: {' '.join(cmd)}")

        # Zapusk pytest v direktorii proekta
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        # Proveryaem rezul'tat
        # Kod 0 = vse testy proshli, kod 1 = est' upavshie testy
        # Oba sluchaya schitaem uspeshnymi dlya nashih tseley
        if result.returncode in (0, 1):
            print("Pytest completed successfully")
            return True
        else:
            print(f"Pytest failed with code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return False
