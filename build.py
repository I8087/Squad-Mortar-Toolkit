import os, sys, shutil
import PyInstaller.__main__

build_scripts = ("smc", "mc", "fdc")

# This build script only supports win32 at the moment.
if sys.platform != "win32":
    print("Only supports building win32!")
    exit(-1)

# Build each of our python scripts.
for i in build_scripts:

    # Build the program.
    PyInstaller.__main__.run(
        ["--clean",
         "--noconsole",
         "--onefile",
         "-n{}".format(i),
         os.path.join(os.getcwd(), "src", "{}.py".format(i))
         ])

    # Clean up spec file.
    if os.path.exists("{}.spec".format(i)):
        try:
            os.remove("{}.spec".format(i))
        except:
            exit(-1)

# Clean up the __pycache__ and build directory.
for i in (os.path.join(os.getcwd(), "src", "__pycache__"), "build"):
    if os.path.exists(i):
        try:
            shutil.rmtree(i)
        except:
            exit(-1)

# Now make our final build directory. This is where the archive will go.
os.mkdir("build")

# Move over the programs into the build directory.
for i in build_scripts:
    shutil.copy2(os.path.join("dist", "{}.exe".format(i)),
                 os.path.join("build", "{}.exe".format(i)))

# Move the rest of the required files into the dist directory.
# They will be bundled together into one archive.
for i in ("CHANGELOG.md", "LICENSE", "README.md"):
    shutil.copy2(i, os.path.join("dist", "{}".format(i)))

# Archive the files.
shutil.make_archive(os.path.join("build", "Squad-Mortar-Toolkit-{}".format(sys.platform)), "zip", "dist")

# Remove the dist directory.
# Clean up the __pycache__ and build directory.
if os.path.exists("dist"):
    try:
        shutil.rmtree("dist")
    except:
        exit(-1)

print("Successfully built the toolkit!...")
