#include <stdlib.h>
#include <iostream>
#include <string>

using namespace std;

int main(int argc, char const *argv[])
{
    string msg;
    string branch;
    string cmd;

    if (argc < 2)
    {
        cout << "Usage: deploy.exe \"commit message\" \"branch (default = main)\"" << endl;
        return 1;
    }

    if (argc > 2)
    {
        branch = argv[2];
    }
    else
    {
        branch = "main";
    }

    msg = argv[1];
    cmd = "hexo clean && hexo g && hexo d && git add . && git commit -m \"" + msg + "\" && git push origin HEAD:" + branch;
    system(cmd.c_str());
    return 0;
}
