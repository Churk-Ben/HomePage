#include <stdlib.h>
#include <iostream>
#include <string>

using namespace std;

int main(int argc, char const *argv[])
{
    if (argc < 2)
    {
        cout << "Usage: deploy.exe \"commit message\"" << endl;
        return 1;
    }

    string msg = argv[1];
    string cmd = "npm run deploy && git add . && git commit -m \"" + msg + "\" && git push origin HEAD:main";
    system(cmd.c_str());
    return 0;
}
