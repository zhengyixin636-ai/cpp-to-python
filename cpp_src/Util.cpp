//////////////////////////////////////////////////////////////////////////
#include "stdafx.h"
#include "Util.h"
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <io.h>
#include <Windows.h>
#include <string>
using namespace std;


///*	**************************************************************************************************************************************		*///
///*															getExtension																									*///
///*	**************************************************************************************************************************************		*///
string Util::getExtension(string path)
{
	int length = path.length();
	int index = 0;
	index = path.rfind(".");

	if (index == -1)
	{
		return "";
	}

	string ext = path.substr(index , length - index);

	transform(ext.begin() , ext.end() , ext.begin() , towlower);
	return ext;
}
///*	**************************************************************************************************************************************		*///
///*																	getDir																									*///
///*	**************************************************************************************************************************************		*///
string Util::getDir(string path)
{
	int length = path.length();
	int index = 0;
	index = path.rfind("\\");

	if (index == -1)
	{
		return "";
	}

	string dir = path.substr(0 , index) ;//+ "\\";

	return dir;
}
///*	**************************************************************************************************************************************		*///
///*															getFileName																									*///
///*	**************************************************************************************************************************************		*///
string Util::getFileName(string path)
{
	int length = path.length();
	int index = 0;
	index = path.rfind("\\");

	if (index == -1)
	{
		return "";
	}

	string fullName = path.substr(index+1, length - index-1);
	index = fullName.rfind(".");
	if (index == -1)
	{
		return "";
	}

	string fileName = fullName.substr(0 , index);
	return fileName;
}
///*	**************************************************************************************************************************************		*///
///*															toString																											*///
///*	**************************************************************************************************************************************		*///
template <class T>
string Util::toString(T value)
{
	stringstream ss;
	ss << value;
	return ss.str();
}
///*	**************************************************************************************************************************************		*///
///*															double2String																								*///
///*	**************************************************************************************************************************************		*///
string Util::double2String(double value)
{
	stringstream ss;
	ss << value;
	return ss.str();
}
///*	**************************************************************************************************************************************		*///
///*															Ansi2WChar																									*///
///*	**************************************************************************************************************************************		*///
////From VpCore
wstring Util::Ansi2WChar( LPCSTR pszSrc, int nLen )
{
	int nSize = MultiByteToWideChar(CP_ACP, 0, (LPCSTR)pszSrc, nLen, 0, 0);
	if(nSize <= 0)
		return NULL;
	WCHAR *pwszDst = new WCHAR[nSize+1];
	if( NULL == pwszDst)
		return NULL;
	MultiByteToWideChar(CP_ACP, 0,(LPCSTR)pszSrc, nLen, pwszDst, nSize);
	pwszDst[nSize] = 0;
	if( pwszDst[0] == 0xFEFF) // skip Oxfeff
		for(int i = 0; i < nSize; i ++) 
			pwszDst[i] = pwszDst[i+1]; 
	wstring wcharString(pwszDst);
	delete []pwszDst;
	return wcharString;
}
///*	**************************************************************************************************************************************		*///
///*															WChar2Ansi																									*///
///*	**************************************************************************************************************************************		*///
string Util::WChar2Ansi( LPCWSTR pwszSrc )
{
	int nLen = WideCharToMultiByte(CP_ACP, 0, pwszSrc, -1, NULL, 0, NULL, NULL);
	if (nLen<= 0) 
		return std::string("");
	char* pszDst = new char[nLen];
	if (NULL == pszDst) 
		return std::string("");
	WideCharToMultiByte(CP_ACP, 0, pwszSrc, -1, pszDst, nLen, NULL, NULL);
	pszDst[nLen -1] = 0;
	std::string strTemp(pszDst);
	delete [] pszDst;
	return strTemp;
}
///*	**************************************************************************************************************************************		*///
///*															itos																												*///
///*	**************************************************************************************************************************************		*///
string Util::itos( int index)
{
	char temp[200];
	sprintf(temp , "%d",index);
	string s(temp);
	return s;
}
///*	**************************************************************************************************************************************		*///
///*															folderExist			判断文件夹是否存在																	*///
///*	**************************************************************************************************************************************		*///
//bool Util::folderExist(const string &strPath)
//{
//	WIN32_FIND_DATA wfd;
//	bool isExisted = false;
//// 	MultiByteToWideChar(CP_ACP , NULL , strPath.c_str() , strlen(strPath.c_str()) , )
//	HANDLE hFind = FindFirstFile(Character::s2ws(strPath).c_str(), &wfd);
//	if ( (hFind != INVALID_HANDLE_VALUE ) && (wfd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY))
//	{
//		isExisted =true;
//	}
//	FindClose(hFind);
//	return isExisted;
//}
///*	**************************************************************************************************************************************		*///
///*															GetFileCount			获取文件数量																		*///
///*	**************************************************************************************************************************************		*///
//int Util::GetFileCount(string strPath , string filter)
//{
///* ---------------------------------------------------------------------------------------------------------------------------------------*/
///*                                                   路径不存在，则返回-1						                                                                    */
///* ---------------------------------------------------------------------------------------------------------------------------------------*/
//	if(!Util::folderExist(strPath))	return -1;
//
//	int fileCount = 0;
//	string path = strPath + "\\" + filter;
//	_finddata_t find;
//	long handle = _findfirst(path.c_str() , &find);
//	if (handle != -1)
//	{
//		do 
//		{
//			string fileFullName = find.name;
//			if(fileFullName == "." || fileFullName == "..")	continue;
//			fileCount++;
//		} while (!_findnext(handle, &find));
//	}
//	_findclose(handle);
//	return fileCount;
//}
